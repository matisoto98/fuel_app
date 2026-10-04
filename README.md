# Calculadora de Combustible

Aplicación web, pensada para el móvil, que estima la autonomía del depósito, los días que dura el combustible, el coste de llenar el tanque y la fecha del próximo repostaje.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Servidor

```bash
uvicorn app.main:app --reload
```

Abrir http://127.0.0.1:8000/docs.

## Despliegue en Render

1. Sube el proyecto a un repositorio privado de GitHub.
2. En Render, entra en New y elige Blueprint.
3. Selecciona el repositorio, rellena `NOMINATIM_CONTACT` y despliega.

El plan gratuito se duerme tras unos 15 minutos sin visitas. La primera visita después tarda unos 30 a 60 segundos.
