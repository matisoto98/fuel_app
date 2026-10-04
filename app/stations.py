"""Nearest stations from the ministry's terrestrial price list."""

import asyncio
import time

import httpx

from app.geo import haversine_km

FUEL_FIELDS = {
    "gasolina95": "Precio Gasolina 95 E5",
    "gasolina98": "Precio Gasolina 98 E5",
    "diesel": "Precio Gasoleo A",
}

_URL = (
    "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/"
    "PreciosCarburantes/EstacionesTerrestres/"
)
_TTL = 30 * 60

updated_at = ""
_stations: list[dict] | None = None
_cached_at = 0.0
_lock: asyncio.Lock | None = None
_lock_loop: asyncio.AbstractEventLoop | None = None


def parse_es_number(value: str) -> float | None:
    text = value.strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _ministry_lock() -> asyncio.Lock:
    global _lock, _lock_loop
    loop = asyncio.get_running_loop()
    if _lock is None or _lock_loop is not loop:
        _lock = asyncio.Lock()
        _lock_loop = loop
    return _lock


async def _download_stations() -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(_URL)
        response.raise_for_status()
        return response.json()


async def fetch_all_stations() -> list[dict]:
    global updated_at, _stations, _cached_at
    if _stations is not None and time.monotonic() - _cached_at < _TTL:
        return _stations
    async with _ministry_lock():
        if _stations is not None and time.monotonic() - _cached_at < _TTL:
            return _stations
        try:
            payload = await _download_stations()
        except Exception:
            if _stations is not None:
                return _stations
            raise
        updated_at = payload.get("Fecha", "")
        _stations = payload.get("ListaEESSPrecio") or []
        _cached_at = time.monotonic()
        return _stations


def find_nearest(stations, lat, lon, fuel, radius_km=10, limit=5) -> list[dict]:
    price_key = FUEL_FIELDS[fuel]
    found = []
    for station in stations:
        slat = parse_es_number(station.get("Latitud") or "")
        slon = parse_es_number(station.get("Longitud (WGS84)") or "")
        price = parse_es_number(station.get(price_key) or "")
        if slat is None or slon is None or price is None:
            continue
        distance = haversine_km(lat, lon, slat, slon)
        if distance > radius_km:
            continue
        found.append(
            (
                distance,
                {
                    "id": station.get("IDEESS"),
                    "name": station.get("Rótulo"),
                    "address": station.get("Dirección"),
                    "town": station.get("Municipio"),
                    "hours": station.get("Horario"),
                    "lat": slat,
                    "lon": slon,
                    "price": price,
                    "distance_km": round(distance, 1),
                },
            )
        )
    found.sort(key=lambda item: item[0])
    return [item[1] for item in found[:limit]]
