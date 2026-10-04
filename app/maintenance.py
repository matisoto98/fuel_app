"""Maintenance reminders. Intervals are guidance; brand and model are labels."""

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta
from math import floor

SIN_DATOS = "Indica cuándo lo hiciste por última vez"

DEFAULT_ITEMS = {
    "aceite": {
        "label": "Cambio de aceite y filtro",
        "interval_km": 15000,
        "interval_months": 12,
    },
    "filtro_aire": {
        "label": "Filtro de aire",
        "interval_km": 30000,
        "interval_months": 24,
    },
    "filtro_habitaculo": {
        "label": "Filtro de habitáculo (polen)",
        "interval_km": 15000,
        "interval_months": 12,
    },
    "frenos": {
        "label": "Revisión de frenos",
        "interval_km": 30000,
        "interval_months": 24,
    },
    "neumaticos": {
        "label": "Revisión y rotación de neumáticos",
        "interval_km": 10000,
        "interval_months": 12,
    },
    "liquido_frenos": {
        "label": "Líquido de frenos",
        "interval_km": None,
        "interval_months": 24,
    },
    "distribucion": {
        "label": "Correa de distribución",
        "interval_km": 120000,
        "interval_months": 60,
        "note": "Varía mucho según el modelo: consulta el manual",
    },
}


@dataclass
class MaintenanceInput:
    brand: str
    model: str
    year: int
    registration_date: date
    current_km: int
    km_per_day: float
    today: date = field(default_factory=date.today)
    items: dict = field(default_factory=dict)


def add_months(start: date, months: int) -> date:
    index = start.month - 1 + months
    year = start.year + index // 12
    month = index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _validate(data: MaintenanceInput) -> None:
    max_year = data.today.year + 1
    if not 1980 <= data.year <= max_year:
        raise ValueError(f"El año debe estar entre 1980 y {max_year}")
    if not 0 <= data.current_km <= 1_000_000:
        raise ValueError("Los kilómetros actuales deben estar entre 0 y 1000000")
    if data.km_per_day <= 0:
        raise ValueError("Los kilómetros por día deben ser mayores que 0")
    for override in data.items.values():
        last_km = override.get("last_km")
        last_date = override.get("last_date")
        if last_km is not None and last_km > data.current_km:
            raise ValueError(
                "Los kilómetros del último mantenimiento no pueden superar los actuales"
            )
        if last_date is not None and last_date > data.today:
            raise ValueError("La fecha del último mantenimiento no puede ser futura")


def _status(due: date | None, today: date, km_remaining: int | None) -> str:
    if due is None:
        return "sin_datos"
    if due <= today:
        return "vencido"
    if (due - today).days <= 30 or (km_remaining is not None and km_remaining <= 1000):
        return "pronto"
    return "ok"


def _item_result(key, label, due, reason, km_remaining, status, note):
    return {
        "key": key,
        "label": label,
        "due_date": due,
        "reason": reason,
        "km_remaining": km_remaining,
        "status": status,
        "note": note,
    }


def _next_itv(registration: date, today: date) -> date:
    due = add_months(registration, 48)
    ten_years = add_months(registration, 120)
    while due < today:
        due = add_months(due, 24 if due < ten_years else 12)
    return due


def schedule(data: MaintenanceInput) -> list[dict]:
    _validate(data)
    results = []
    for key, spec in DEFAULT_ITEMS.items():
        override = data.items.get(key, {})
        interval_km = override["interval_km"] if "interval_km" in override else spec["interval_km"]
        interval_months = (
            override["interval_months"] if "interval_months" in override else spec["interval_months"]
        )
        last_km = override.get("last_km")
        last_date = override.get("last_date")
        due_km = None
        km_remaining = None
        if last_km is not None and interval_km is not None:
            km_remaining = last_km + interval_km - data.current_km
            days = floor(km_remaining / data.km_per_day)
            due_km = data.today + timedelta(days=days)
        due_time = add_months(last_date, interval_months) if last_date is not None and interval_months is not None else None
        if due_km is not None and (due_time is None or due_km <= due_time):
            due, reason = due_km, "km"
        elif due_time is not None:
            due, reason = due_time, "tiempo"
        else:
            due, reason = None, None
        status = _status(due, data.today, km_remaining)
        note = spec.get("note")
        if status == "sin_datos":
            note = f"{SIN_DATOS}. {note}" if note else SIN_DATOS
        results.append(_item_result(key, spec["label"], due, reason, km_remaining, status, note))

    itv_due = _next_itv(data.registration_date, data.today)
    results.append(
        _item_result("itv", "ITV", itv_due, "tiempo", None, _status(itv_due, data.today, None), None)
    )
    results.sort(key=lambda item: (item["due_date"] is None, item["due_date"] or date.min))
    return results
