"""Pure fuel-range calculations. No I/O."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from math import floor

_CHECKS = (
    (
        "tank_capacity_l",
        200,
        "La capacidad del tanque debe ser mayor que 0",
        "La capacidad del tanque no puede superar 200 L",
    ),
    (
        "consumption_l_per_100km",
        50,
        "El consumo debe ser mayor que 0",
        "El consumo no puede superar 50 L/100 km",
    ),
    (
        "km_per_day",
        2000,
        "Los kilómetros por día deben ser mayores que 0",
        "Los kilómetros por día no pueden superar 2000",
    ),
    (
        "price_per_l",
        10,
        "El precio por litro debe ser mayor que 0",
        "El precio por litro no puede superar 10",
    ),
)


@dataclass
class FuelInput:
    tank_capacity_l: float
    consumption_l_per_100km: float
    km_per_day: float
    price_per_l: float
    start_date: date = field(default_factory=date.today)


@dataclass
class FuelResult:
    range_km: float
    days_lasting: float
    full_tank_cost: float
    next_refuel_date: date


def calculate(data: FuelInput) -> FuelResult:
    for name, limit, non_positive_msg, too_large_msg in _CHECKS:
        value = getattr(data, name)
        if value <= 0:
            raise ValueError(non_positive_msg)
        if value > limit:
            raise ValueError(too_large_msg)

    range_km = round(data.tank_capacity_l / data.consumption_l_per_100km * 100, 1)
    raw_days = range_km / data.km_per_day
    return FuelResult(
        range_km=range_km,
        days_lasting=round(raw_days, 1),
        full_tank_cost=round(data.tank_capacity_l * data.price_per_l, 2),
        next_refuel_date=data.start_date + timedelta(days=floor(raw_days)),
    )
