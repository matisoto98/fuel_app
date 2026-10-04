import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.main import app

SAMPLE = Path(__file__).parent / "fixtures" / "stations_sample.json"

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Calculadora de Combustible" in response.text


def test_security_headers():
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["permissions-policy"] == "geolocation=(self)"


def test_static_css():
    response = client.get("/static/css/styles.css")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_calcular_example():
    response = client.post(
        "/api/calcular",
        json={
            "tank_capacity_l": 80,
            "consumption_l_per_100km": 8,
            "km_per_day": 50,
            "price_per_l": 1.60,
            "start_date": "2026-10-04",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "range_km": 1000.0,
        "days_lasting": 20.0,
        "full_tank_cost": 128.0,
        "next_refuel_date": "2026-10-24",
    }


def test_calcular_invalid_tank():
    response = client.post(
        "/api/calcular",
        json={
            "tank_capacity_l": 0,
            "consumption_l_per_100km": 8,
            "km_per_day": 50,
            "price_per_l": 1.60,
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "La capacidad del tanque debe ser mayor que 0"}


def test_calcular_missing_field():
    response = client.post(
        "/api/calcular",
        json={
            "consumption_l_per_100km": 8,
            "km_per_day": 50,
            "price_per_l": 1.60,
        },
    )
    assert response.status_code == 422


def _patch_geocoders(monkeypatch, nominatim, cartociudad):
    monkeypatch.setattr("app.geo._cache", {})
    monkeypatch.setattr("app.geo._last_request", 0.0)
    monkeypatch.setattr("app.geo._nominatim_search", nominatim)
    monkeypatch.setattr("app.geo._cartociudad_search", cartociudad)


def _patch_nominatim(monkeypatch, fake):
    async def unused(address: str):
        raise AssertionError("no debe llamar a CartoCiudad")

    _patch_geocoders(monkeypatch, fake, unused)


def test_ubicacion_ok(monkeypatch):
    async def fake_search(address: str):
        return [
            {
                "lat": "40.42",
                "lon": "-3.70",
                "display_name": "Calle de Alcalá 50, Madrid",
            }
        ]

    _patch_nominatim(monkeypatch, fake_search)
    response = client.get(
        "/api/ubicacion",
        params={"direccion": "Calle de Alcalá 50, Madrid"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "lat": 40.42,
        "lon": -3.70,
        "display_name": "Calle de Alcalá 50, Madrid",
    }


def test_ubicacion_not_found(monkeypatch):
    async def fake_search(address: str):
        return []

    async def no_backup(address: str):
        return None

    _patch_geocoders(monkeypatch, fake_search, no_backup)
    response = client.get(
        "/api/ubicacion",
        params={"direccion": "Calle que no existe 999"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "No encontramos esa dirección en España"}


def test_ubicacion_service_down(monkeypatch):
    async def fake_search(address: str):
        raise httpx.TimeoutException("timeout")

    async def backup_down(address: str):
        raise httpx.TimeoutException("timeout")

    _patch_geocoders(monkeypatch, fake_search, backup_down)
    response = client.get(
        "/api/ubicacion",
        params={"direccion": "Calle de Alcalá 50, Madrid"},
    )
    assert response.status_code == 503
    assert response.json() == {
        "detail": "El servicio de mapas no está disponible, inténtalo de nuevo",
    }


def test_ubicacion_falls_back_when_nominatim_fails(monkeypatch):
    async def fake_search(address: str):
        raise httpx.HTTPStatusError(
            "forbidden",
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/search"),
            response=httpx.Response(403),
        )

    async def backup(address: str):
        return {"lat": 40.41, "lon": -3.69, "display_name": "ALCALA 50, Madrid, Madrid"}

    _patch_geocoders(monkeypatch, fake_search, backup)
    response = client.get("/api/ubicacion", params={"direccion": "Calle de Alcalá 50, Madrid"})
    assert response.status_code == 200
    assert response.json() == {
        "lat": 40.41,
        "lon": -3.69,
        "display_name": "ALCALA 50, Madrid, Madrid",
    }


def test_ubicacion_falls_back_when_nominatim_empty(monkeypatch):
    async def fake_search(address: str):
        return []

    async def backup(address: str):
        return {"lat": 40.41, "lon": -3.69, "display_name": "ALCALA 50, Madrid, Madrid"}

    _patch_geocoders(monkeypatch, fake_search, backup)
    response = client.get("/api/ubicacion", params={"direccion": "Calle de Alcalá 50, Madrid"})
    assert response.status_code == 200
    assert response.json()["display_name"] == "ALCALA 50, Madrid, Madrid"


def _patch_stations(monkeypatch, download):
    monkeypatch.setattr("app.stations._stations", None)
    monkeypatch.setattr("app.stations._cached_at", 0.0)
    monkeypatch.setattr("app.stations.updated_at", "")
    monkeypatch.setattr("app.stations._download_stations", download)


def test_gasolineras_ok(monkeypatch):
    payload = json.loads(SAMPLE.read_text())

    async def fake_download():
        return payload

    _patch_stations(monkeypatch, fake_download)
    response = client.get(
        "/api/gasolineras",
        params={"lat": 40.42, "lon": -3.70, "combustible": "gasolina95"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["combustible"] == "gasolina95"
    assert body["actualizado"] == "04/10/2026 10:00:00"
    assert [item["id"] for item in body["gasolineras"]] == ["1001", "1002", "1003"]
    assert body["mas_barata_id"] == "1002"


def test_gasolineras_bad_fuel(monkeypatch):
    async def fake_download():
        raise AssertionError("no debe llamar al ministerio")

    _patch_stations(monkeypatch, fake_download)
    response = client.get(
        "/api/gasolineras",
        params={"lat": 40.42, "lon": -3.70, "combustible": "queroseno"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Tipo de combustible no válido"}


def test_gasolineras_outside_spain(monkeypatch):
    async def fake_download():
        raise AssertionError("no debe llamar al ministerio")

    _patch_stations(monkeypatch, fake_download)
    response = client.get(
        "/api/gasolineras",
        params={"lat": 48, "lon": 2, "combustible": "gasolina95"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "La ubicación debe estar en España"}


def test_gasolineras_service_down(monkeypatch):
    async def fake_download():
        raise httpx.TimeoutException("down")

    _patch_stations(monkeypatch, fake_download)
    response = client.get(
        "/api/gasolineras",
        params={"lat": 40.42, "lon": -3.70, "combustible": "diesel"},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "No pudimos obtener los precios, inténtalo más tarde"}


def test_ubicacion_too_short(monkeypatch):
    async def fake_search(address: str):
        raise AssertionError("no debe llamar a Nominatim")

    _patch_nominatim(monkeypatch, fake_search)
    response = client.get("/api/ubicacion", params={"direccion": "abc"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Introduce una dirección válida"}


def _mantenimiento_body(**overrides):
    body = {
        "brand": "Seat",
        "model": "Ibiza",
        "year": 2019,
        "registration_date": "2019-05-10",
        "current_km": 50000,
        "km_per_day": 50,
        "today": "2026-10-04",
        "items": {"aceite": {"last_km": 40000, "last_date": "2026-06-01"}},
    }
    body.update(overrides)
    return body


def test_mantenimiento_ok():
    response = client.post("/api/mantenimiento", json=_mantenimiento_body())
    assert response.status_code == 200
    aceite = next(item for item in response.json() if item["key"] == "aceite")
    assert aceite["due_date"] == "2027-01-12"
    assert aceite["reason"] == "km"


def test_mantenimiento_bad_year():
    response = client.post("/api/mantenimiento", json=_mantenimiento_body(year=1970))
    assert response.status_code == 400
    assert response.json() == {"detail": "El año debe estar entre 1980 y 2027"}


def test_mantenimiento_calendario():
    response = client.post("/api/mantenimiento/calendario", json=_mantenimiento_body())
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert response.headers["content-disposition"] == 'attachment; filename="mantenimiento.ics"'
    assert "BEGIN:VCALENDAR" in response.text
