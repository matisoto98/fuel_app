import asyncio

import httpx

from app.geo import geocode_address, haversine_km


def test_haversine_madrid_barcelona():
    distance = haversine_km(40.4168, -3.7038, 41.3874, 2.1686)
    assert 500 <= distance <= 510


def test_haversine_same_point():
    assert haversine_km(40.4168, -3.7038, 40.4168, -3.7038) == 0


def test_geocode_address_uses_cache(monkeypatch):
    calls = {"n": 0}

    async def fake_search(address: str):
        calls["n"] += 1
        return [{"lat": "40.4168", "lon": "-3.7038", "display_name": "Madrid"}]

    async def province(lat, lon):
        return "28"

    monkeypatch.setattr("app.geo._cache", {})
    monkeypatch.setattr("app.geo._last_request", 0.0)
    monkeypatch.setattr("app.geo._nominatim_search", fake_search)
    monkeypatch.setattr("app.geo.province_code", province)

    async def twice():
        first = await geocode_address("Calle Mayor 1, Madrid")
        second = await geocode_address("Calle Mayor 1, Madrid")
        return first, second

    first, second = asyncio.run(twice())
    assert first == {
        "lat": 40.4168,
        "lon": -3.7038,
        "display_name": "Madrid",
        "provincia": "28",
    }
    assert second == first
    assert calls["n"] == 1


def test_user_agent_uses_nominatim_contact(monkeypatch):
    monkeypatch.setenv("NOMINATIM_CONTACT", "yo@example.com")
    seen = {}

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return []

    class _Client:
        def __init__(self, timeout):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params, headers):
            seen["user_agent"] = headers["User-Agent"]
            return _Response()

    monkeypatch.setattr(httpx, "AsyncClient", _Client)
    monkeypatch.setattr("app.geo._cache", {})
    monkeypatch.setattr("app.geo._last_request", 0.0)
    asyncio.run(geocode_address("Calle Mayor 1, Madrid"))
    assert seen["user_agent"] == "CalculadoraCombustible/1.0 (+yo@example.com)"
