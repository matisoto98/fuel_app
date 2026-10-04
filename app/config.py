import os

_DEFAULT_CONTACT = "contacto@calculadoracombustible.local"


def nominatim_user_agent() -> str:
    contact = os.environ.get("NOMINATIM_CONTACT") or _DEFAULT_CONTACT
    return f"CalculadoraCombustible/1.0 (+{contact})"
