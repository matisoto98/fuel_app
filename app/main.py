from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app import stations
from app.calculator import FuelInput, calculate
from app.geo import geocode_address, log_geocoder_failure, province_code
from app.ics import build_ics
from app.maintenance import DEFAULT_ITEMS, MaintenanceInput, schedule

_HERE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=_HERE / "templates")

app = FastAPI(title="Calculadora de Combustible")
app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    return response


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"maintenance_items": DEFAULT_ITEMS},
    )


class MaintenanceItemIn(BaseModel):
    last_km: int | None = None
    last_date: date | None = None
    interval_km: int | None = None
    interval_months: int | None = None


class MaintenanceRequest(BaseModel):
    brand: str
    model: str
    year: int
    registration_date: date
    current_km: int
    km_per_day: float
    today: date = Field(default_factory=date.today)
    items: dict[str, MaintenanceItemIn] = Field(default_factory=dict)


class CalcularRequest(BaseModel):
    tank_capacity_l: float
    consumption_l_per_100km: float
    km_per_day: float
    price_per_l: float
    start_date: date = Field(default_factory=date.today)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/calcular")
def calcular(body: CalcularRequest):
    try:
        result = calculate(FuelInput(**body.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "range_km": result.range_km,
        "days_lasting": result.days_lasting,
        "full_tank_cost": result.full_tank_cost,
        "next_refuel_date": result.next_refuel_date.isoformat(),
    }


@app.get("/api/ubicacion")
async def ubicacion(direccion: str = ""):
    if len(direccion.strip()) < 5:
        raise HTTPException(status_code=400, detail="Introduce una dirección válida")
    try:
        found = await geocode_address(direccion)
    except Exception as exc:
        log_geocoder_failure("nominatim", exc)
        raise HTTPException(
            status_code=503,
            detail="El servicio de mapas no está disponible, inténtalo de nuevo",
        ) from None
    if found is None:
        raise HTTPException(status_code=404, detail="No encontramos esa dirección en España")
    return found


def _in_spain(lat: float, lon: float) -> bool:
    return 27 <= lat <= 44.5 and -18.5 <= lon <= 5


@app.get("/api/provincia")
async def provincia(lat: float, lon: float):
    if not _in_spain(lat, lon):
        raise HTTPException(status_code=400, detail="La ubicación debe estar en España")
    try:
        code = await province_code(lat, lon)
    except Exception as exc:
        log_geocoder_failure("cartociudad", exc)
        raise HTTPException(
            status_code=503,
            detail="El servicio de mapas no está disponible, inténtalo de nuevo",
        ) from None
    if not code:
        raise HTTPException(status_code=404, detail="No pudimos saber tu provincia")
    return {"provincia": code}


@app.get("/api/gasolineras")
async def gasolineras(
    lat: float,
    lon: float,
    combustible: str,
    radio_km: float = Query(default=10, ge=1, le=50),
    limite: int = Query(default=5, ge=1, le=20),
):
    if combustible not in stations.FUEL_FIELDS:
        raise HTTPException(status_code=400, detail="Tipo de combustible no válido")
    if not _in_spain(lat, lon):
        raise HTTPException(status_code=400, detail="La ubicación debe estar en España")
    try:
        rows = await stations.fetch_all_stations()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="No pudimos obtener los precios, inténtalo más tarde",
        ) from None
    nearest = stations.find_nearest(
        rows, lat, lon, combustible, radius_km=radio_km, limit=limite
    )
    cheapest = min(nearest, key=lambda item: item["price"]) if nearest else None
    return {
        "combustible": combustible,
        "actualizado": stations.updated_at,
        "gasolineras": nearest,
        "mas_barata_id": cheapest["id"] if cheapest else None,
    }


def _maintenance_input(body: MaintenanceRequest) -> MaintenanceInput:
    return MaintenanceInput(
        brand=body.brand,
        model=body.model,
        year=body.year,
        registration_date=body.registration_date,
        current_km=body.current_km,
        km_per_day=body.km_per_day,
        today=body.today,
        items={key: item.model_dump(exclude_unset=True) for key, item in body.items.items()},
    )


def _schedule_or_400(body: MaintenanceRequest) -> list[dict]:
    try:
        return schedule(_maintenance_input(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/mantenimiento")
def mantenimiento(body: MaintenanceRequest):
    return _schedule_or_400(body)


@app.post("/api/mantenimiento/calendario")
def mantenimiento_calendario(body: MaintenanceRequest):
    items = _schedule_or_400(body)
    ics = build_ics(items, f"{body.brand} {body.model}".strip())
    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="mantenimiento.ics"'},
    )
