# ESP32-P4 Weather Slideshow

Local-network weather, radar, HAM, and SPC outlook slideshow for the Elecrow CrowPanel Advanced 10.1" ESP32-P4 display. **pinky.local** (TrueNAS) composes data and images; **brain.local** (ESP32-P4) renders them with LVGL.

See [pre-plan.md](pre-plan.md) for product requirements.

## Hostnames

| Host | Role |
|------|------|
| `pinky.local` | TrueNAS SCALE — slideshow API (port **8787**) |
| `brain.local` | ESP32-P4 — LVGL client |

## Repository layout

- [`backend/`](backend/) — FastAPI service (Docker image on GHCR)
- [`deploy/truenas/`](deploy/truenas/) — TrueNAS Custom App Compose
- [`firmware/`](firmware/) — ESP-IDF 5.x project for ESP32-P4
- [`docs/`](docs/) — API contract and install guides

## Quick start — pinky (TrueNAS)

1. Create dataset **`apps/esp32-weather-slideshow`** (under TrueNAS Apps storage); bind mount `/mnt/<pool>/apps/esp32-weather-slideshow` in Compose
2. Install Custom App from [docs/truenas-install.md](docs/truenas-install.md)
3. Verify: `curl http://pinky.local:8787/health`

## Quick start — backend (local dev)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8080
```

Open `http://127.0.0.1:8080/api/v1/slideshow`.

## Quick start — brain (firmware)

Requires [ESP-IDF 5.4+](https://docs.espressif.com/projects/esp-idf/) with ESP32-P4 support.

```bash
cd firmware
idf.py set-target esp32p4
idf.py menuconfig   # WiFi + SLIDESHOW_BASE_URL
idf.py build flash monitor
```

Base on Elecrow’s ESP-IDF examples for MIPI-DSI and GT911 touch; this project wires slideshow logic, HTTP client, and gestures on top.

## API

Documented in [docs/api-v1.md](docs/api-v1.md).

## Integration testing

See [docs/integration-test.md](docs/integration-test.md).

## License

MIT — see [LICENSE](LICENSE).
