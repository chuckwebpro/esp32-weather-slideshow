# Slideshow API (backend)

FastAPI service that polls weather, NWS alerts, NEXRAD, HamQSL, and SPC; caches composited JPEGs under `/data`.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATA_DIR=./data
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Tests

```bash
pytest
```
