import asyncio
import json
import time
from pathlib import Path

import httpx

from app.stations import fetch_all_stations, find_nearest, parse_es_number

SAMPLE = Path(__file__).parent / "fixtures" / "stations_sample.json"
ORIGIN = (40.42, -3.70)


def _stations():
    return json.loads(SAMPLE.read_text())["ListaEESSPrecio"]


def _patch_download(monkeypatch, download):
    monkeypatch.setattr("app.stations._stations", None)
    monkeypatch.setattr("app.stations._cached_at", 0.0)
    monkeypatch.setattr("app.stations.updated_at", "")
    monkeypatch.setattr("app.stations._download_stations", download)


def test_parse_es_number():
    assert parse_es_number("1,589") == 1.589
    assert parse_es_number("") is None
    assert parse_es_number("no-es-numero") is None


def test_find_nearest_sorts_within_radius():
    found = find_nearest(_stations(), *ORIGIN, "gasolina95", radius_km=2, limit=5)
    assert [item["id"] for item in found] == ["1001", "1002"]
    assert [item["distance_km"] for item in found] == [0.0, 1.1]
    assert found[0]["name"] == "Cerca"
    assert found[0]["address"] == "CALLE MAYOR 1"
    assert found[0]["town"] == "Madrid"
    assert found[0]["hours"] == "L-D: 24H"
    assert found[0]["price"] == 1.599


def test_find_nearest_skips_missing_diesel_price():
    found = find_nearest(_stations(), *ORIGIN, "diesel", radius_km=10, limit=5)
    assert [item["id"] for item in found] == ["1001", "1003"]


def test_fetch_all_stations_uses_cache(monkeypatch):
    calls = {"n": 0}
    payload = json.loads(SAMPLE.read_text())

    async def fake_download():
        calls["n"] += 1
        return payload

    _patch_download(monkeypatch, fake_download)

    async def twice():
        first = await fetch_all_stations()
        second = await fetch_all_stations()
        return first, second

    first, second = asyncio.run(twice())
    assert first == second
    assert calls["n"] == 1


def test_fetch_keeps_stale_cache_when_refresh_fails(monkeypatch):
    calls = {"n": 0}
    payload = json.loads(SAMPLE.read_text())

    async def fake_download():
        calls["n"] += 1
        if calls["n"] > 1:
            raise httpx.TimeoutException("down")
        return payload

    _patch_download(monkeypatch, fake_download)

    async def run():
        import app.stations as stations

        first = await fetch_all_stations()
        stations._cached_at = time.monotonic() - stations._TTL - 1
        second = await fetch_all_stations()
        return first, second

    first, second = asyncio.run(run())
    assert calls["n"] == 2
    assert second == first
