# brain.local — ESP32-P4 firmware

Slideshow client for the Elecrow CrowPanel Advanced 10.1" (ESP32-P4 + C6 WiFi).

## Prerequisites

- [ESP-IDF 5.4+](https://docs.espressif.com/projects/esp-idf/) with **esp32p4** support
- Elecrow ESP-IDF examples for MIPI-DSI display + GT911 touch
- pinky slideshow API at `http://pinky.local:8787` (see [truenas-install.md](truenas-install.md))

## Configure

```bash
cd firmware
idf.py set-target esp32p4
idf.py menuconfig
```

**Slideshow**

- `SLIDESHOW_BASE_URL` → `http://pinky.local:8787`
- WiFi SSID / password
- Poll and advance intervals (defaults match pinky)

**PSRAM** — enable in *Component config → ESP PSRAM* (required for 1024×600 JPEG decode).

## Integrate Elecrow BSP

Replace the stub in [`firmware/components/crowpanel/crowpanel_board.c`](../firmware/components/crowpanel/crowpanel_board.c) with Elecrow’s display/touch/LVGL port init. Until then, UI logic runs but the panel may not light up.

## Build and flash

```bash
idf.py build flash monitor
```

On boot, **brain** should join WiFi, poll `/api/v1/slideshow`, auto-advance every 10 s, and load radar/outlook JPEGs from pinky.

## Interaction (pre-plan)

- Tap: pause / resume
- Swipe left/right while paused: change slide
- Pinch on image slides: zoom (basic)

## Troubleshooting

| Issue | Check |
|-------|--------|
| No data | `ping pinky.local` from LAN; URL in menuconfig |
| JPEG slides blank | PSRAM enabled; serial log `image_loader` / `esp_jpeg` |
| WiFi fails | SSID/password; 2.4 GHz |
| Old slides after pinky update | Normal; brain polls every ~45 s |

## Integration checklist

See [integration-test.md](integration-test.md) — **brain.local** section.
