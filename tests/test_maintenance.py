from datetime import date

import pytest

from app.ics import build_ics
from app.maintenance import MaintenanceInput, schedule

TODAY = date(2026, 10, 4)


def sample(**kwargs) -> MaintenanceInput:
    data = {
        "brand": "Seat",
        "model": "Ibiza",
        "year": 2019,
        "registration_date": date(2019, 5, 10),
        "current_km": 50000,
        "km_per_day": 50,
        "today": TODAY,
        "items": {},
    }
    data.update(kwargs)
    return MaintenanceInput(**data)


def by_key(result, key):
    return next(item for item in result if item["key"] == key)


def test_oil_due_by_km_first():
    result = schedule(
        sample(
            items={"aceite": {"last_km": 40000, "last_date": date(2026, 6, 1)}},
        )
    )
    aceite = by_key(result, "aceite")
    assert aceite["km_remaining"] == 5000
    assert aceite["due_date"] == date(2027, 1, 12)
    assert aceite["reason"] == "km"
    assert [item["due_date"] is None for item in result] == sorted(
        [item["due_date"] is None for item in result]
    )


def test_oil_due_by_time_first():
    result = schedule(
        sample(
            current_km=50000,
            km_per_day=10,
            items={"aceite": {"last_km": 49000, "last_date": date(2025, 11, 1)}},
        )
    )
    aceite = by_key(result, "aceite")
    assert aceite["due_date"] == date(2026, 11, 1)
    assert aceite["reason"] == "tiempo"
    assert aceite["status"] == "pronto"


def test_overdue_item_is_vencido():
    result = schedule(
        sample(
            items={"aceite": {"last_km": 40000, "last_date": date(2025, 1, 1)}},
        )
    )
    assert by_key(result, "aceite")["status"] == "vencido"


def test_item_without_history_is_sin_datos():
    result = schedule(sample())
    aire = by_key(result, "filtro_aire")
    assert aire["status"] == "sin_datos"
    assert aire["due_date"] is None
    assert aire["note"] == "Indica cuándo lo hiciste por última vez"
    assert result[-1]["due_date"] is None


@pytest.mark.parametrize(
    ("registered", "expected"),
    [
        (date(2019, 5, 10), date(2027, 5, 10)),
        (date(2014, 3, 1), date(2027, 3, 1)),
        (date(2024, 1, 15), date(2028, 1, 15)),
    ],
)
def test_itv_next_date(registered, expected):
    result = schedule(sample(year=registered.year, registration_date=registered))
    itv = by_key(result, "itv")
    assert itv["label"] == "ITV"
    assert itv["due_date"] == expected
    assert itv["km_remaining"] is None


def test_month_end_clamps_to_last_day():
    result = schedule(
        sample(
            items={"aceite": {"last_date": date(2024, 1, 31), "interval_months": 1}},
        )
    )
    assert by_key(result, "aceite")["due_date"] == date(2024, 2, 29)


def test_ics_lists_dated_items_with_crlf():
    items = schedule(
        sample(items={"aceite": {"last_km": 40000, "last_date": date(2026, 6, 1)}})
    )
    ics = build_ics(items, "Seat Ibiza")
    dated = [item for item in items if item["due_date"] is not None]
    assert "BEGIN:VCALENDAR" in ics
    assert ics.count("BEGIN:VEVENT") == len(dated)
    assert "BEGIN:VALARM" in ics
    assert "TRIGGER:-P3D" in ics
    assert "\r\n" in ics
    assert "\n" not in ics.replace("\r\n", "")
    escaped = build_ics(items, "A, B; C")
    assert "A\\, B\\; C" in escaped
