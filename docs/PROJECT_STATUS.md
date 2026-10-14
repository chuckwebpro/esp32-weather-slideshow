# Project status

**Last updated:** 2026-10-14  
**Resume when:** Elecrow CrowPanel Advanced 10.1" (ESP32-P4) arrives.

## Hostnames

| Host | Role | Status |
|------|------|--------|
| **pinky.local** | TrueNAS SCALE — slideshow API `:8787` | **Running** |
| **brain.local** | ESP32-P4 — LVGL client | **Firmware not flashed yet** (no hardware) |

## Done — pinky (backend)

- [x] Custom App on TrueNAS (`apps/esp32-weather-slideshow` → `/mnt/apps/esp32-weather-slideshow`)
- [x] GHCR image `ghcr.io/chuckwebpro/esp32-weather-slideshow-api:latest`
- [x] Compose: `pull_policy: always`, ridge env URLs, `RIDGE_OFFSET_KM_EAST` (~10 mi) tuned for local AOI
- [x] Live slides: weather (Open-Meteo), HAM (HamQSL), SPC Day 1 + **CONUS state basemap**, KFWS reflectivity + **base_velocity** radar (geographic crop)
- [x] NWS alerts in JSON (audio on brain still TODO)
- [x] Verify: `curl http://pinky.local:8787/health` → check `api_version`, `spc_basemap_bundled`, `spc_revision`

**Updating pinky:** Apps → Installed → **Upgrade** or Edit YAML → Save (avoid full reinstall if possible). See [truenas-install.md](truenas-install.md).

## In progress — brain (firmware)

Code is on `main` under [`firmware/`](../firmware/); **not validated on hardware yet**.

- [x] Project skeleton: HTTP client, manifest parse, slideshow UI shell, gestures (tap pause, swipe when paused, pinch hook)
- [x] WiFi STA (menuconfig SSID/password under **Slideshow**)
- [x] JPEG download + `esp_jpeg` decode path for radar/outlook slides
- [x] Poll pinky without resetting slide index on each refresh
- [ ] **Elecrow BSP** — replace stub in [`firmware/components/crowpanel/crowpanel_board.c`](../firmware/components/crowpanel/crowpanel_board.c) (MIPI-DSI 1024×600, GT911, LVGL port, C6 WiFi if required by their example)
- [ ] **PSRAM** in menuconfig (required for full-size JPEG buffers)
- [ ] First `idf.py build flash monitor` on real board
- [ ] I2S WAV for SVR/TOR ([`firmware/main/audio/alert_audio.c`](../firmware/main/audio/alert_audio.c) is stub + NVS dedupe)
- [ ] HAM band detail lines on UI (summary only today)
- [ ] Home Assistant slide (post–v1)

**Start here tomorrow:** [brain-setup.md](brain-setup.md) → Elecrow example → menuconfig → flash → [integration-test.md](integration-test.md) (brain section).

## API contract

Shared by pinky and brain: [api-v1.md](api-v1.md).  
Default brain URL: `http://pinky.local:8787`

## Product brief

Original requirements: [pre-plan.md](../pre-plan.md).

## Open / later

- MQTT push (optional; HTTP poll is enough for v1)
- Pinch pan while zoomed
- Pin GHCR image to SHA for reproducible pinky deploys (optional)
