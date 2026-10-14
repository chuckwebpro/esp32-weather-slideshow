# ESP32-P4 firmware (brain.local)

ESP-IDF 5.4+ project for the Elecrow CrowPanel Advanced 10.1" ESP32-P4.

Full guide: [docs/brain-setup.md](../docs/brain-setup.md).

## Setup

1. Install ESP-IDF with **esp32p4** support.
2. Copy display/touch init from Elecrow’s ESP-IDF examples into [`components/crowpanel/crowpanel_board.c`](components/crowpanel/crowpanel_board.c) (marked `TODO`).
3. Configure WiFi and slideshow URL:

   ```bash
   idf.py menuconfig
   # Slideshow → Base URL, WiFi SSID/password
   ```

4. Enable **PSRAM** in menuconfig for 1024×600 JPEG slides.

5. Build and flash:

   ```bash
   idf.py set-target esp32p4
   idf.py build flash monitor
   ```

## Features

- Polls pinky `GET /api/v1/slideshow`; keeps current slide on refresh
- Weather + HAM screens; radar/outlook JPEG download + decode (`esp_jpeg` component)
- 10 s auto-advance; tap pause; swipe when paused; pinch zoom on images
- I2S alert stubs for SVR/TOR (NVS dedupe) — add WAV + pins in `alert_audio.c`
