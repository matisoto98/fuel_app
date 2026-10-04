"""Address geocoding. The address lives only in the in-memory cache."""

import asyncio
import time
from math import atan2, cos, radians, sin, sqrt

import httpx

from app.config import nominatim_user_agent

_NOMINATIM = "https://nominatim.openstreetmap.org/search"

_cache: dict[str, dict | None] = {}
_last_request = 0.0
_lock: asyncio.Lock | None = None
_lock_loop: asyncio.AbstractEventLoop | None = None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * radius * atan2(sqrt(a), sqrt(1 - a))


def _nominatim_lock() -> asyncio.Lock:
    global _lock, _lock_loop
    loop = asyncio.get_running_loop()
    if _lock is None or _lock_loop is not loop:
        _lock = asyncio.Lock()
        _lock_loop = loop
    return _lock


async def _nominatim_search(address: str) -> list:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _NOMINATIM,
            params={
                "q": address,
                "format": "jsonv2",
                "countrycodes": "es",
                "limit": 1,
                "addressdetails": 0,
            },
            headers={"User-Agent": nominatim_user_agent()},
        )
        response.raise_for_status()
        return response.json()


async def geocode_address(address: str) -> dict | None:
    global _last_request
    key = " ".join(address.lower().split())
    if key in _cache:
        return _cache[key]

    async with _nominatim_lock():
        if key in _cache:
            return _cache[key]
        wait = 1.0 - (time.monotonic() - _last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request = time.monotonic()
        results = await _nominatim_search(address)
        if not results:
            found = None
        else:
            hit = results[0]
            found = {
                "lat": float(hit["lat"]),
                "lon": float(hit["lon"]),
                "display_name": hit["display_name"],
            }
        _cache[key] = found
        return found
