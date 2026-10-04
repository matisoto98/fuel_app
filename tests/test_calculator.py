from datetime import date

import pytest

from app.calculator import FuelInput, calculate


def test_example_case():
    result = calculate(
        FuelInput(
            tank_capacity_l=80,
            consumption_l_per_100km=8,
            km_per_day=50,
            price_per_l=1.60,
            start_date=date(2026, 10, 4),
        )
    )
    assert result.range_km == 1000.0
    assert result.days_lasting == 20.0
    assert result.full_tank_cost == 128.00
    assert result.next_refuel_date == date(2026, 10, 24)


def test_fractional_days_floor_refuel_date():
    # 55 L at 10 L/100 km -> 550 km; 550 / 30 = 18.333... days -> 18.3; floor adds 18 days.
    result = calculate(
        FuelInput(
            tank_capacity_l=55,
            consumption_l_per_100km=10,
            km_per_day=30,
            price_per_l=1.5,
            start_date=date(2026, 10, 4),
        )
    )
    assert result.range_km == 550.0
    assert result.days_lasting == 18.3
    assert result.next_refuel_date == date(2026, 10, 22)


def test_refuel_date_floors_unrounded_days():
    # 1000 km / 52.74 = 18.9609... -> days_lasting 19.0, but the date adds 18 days.
    result = calculate(
        FuelInput(
            tank_capacity_l=80,
            consumption_l_per_100km=8,
            km_per_day=52.74,
            price_per_l=1.60,
            start_date=date(2026, 10, 4),
        )
    )
    assert result.days_lasting == 19.0
    assert result.next_refuel_date == date(2026, 10, 22)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("tank_capacity_l", 0, "La capacidad del tanque debe ser mayor que 0"),
        ("tank_capacity_l", -1, "La capacidad del tanque debe ser mayor que 0"),
        ("tank_capacity_l", 201, "La capacidad del tanque no puede superar 200 L"),
        ("consumption_l_per_100km", 0, "El consumo debe ser mayor que 0"),
        ("consumption_l_per_100km", -0.1, "El consumo debe ser mayor que 0"),
        ("consumption_l_per_100km", 51, "El consumo no puede superar 50 L/100 km"),
        ("km_per_day", 0, "Los kilómetros por día deben ser mayores que 0"),
        ("km_per_day", -5, "Los kilómetros por día deben ser mayores que 0"),
        ("km_per_day", 2001, "Los kilómetros por día no pueden superar 2000"),
        ("price_per_l", 0, "El precio por litro debe ser mayor que 0"),
        ("price_per_l", -2, "El precio por litro debe ser mayor que 0"),
        ("price_per_l", 10.01, "El precio por litro no puede superar 10"),
    ],
)
def test_validation_errors(field, value, message):
    data = {
        "tank_capacity_l": 80,
        "consumption_l_per_100km": 8,
        "km_per_day": 50,
        "price_per_l": 1.60,
        "start_date": date(2026, 10, 4),
    }
    data[field] = value
    with pytest.raises(ValueError, match=message):
        calculate(FuelInput(**data))
