# ESP32-P4 firmware (brain.local)

ESP-IDF 5.4+ project for the Elecrow CrowPanel Advanced 10.1" ESP32-P4.

## Setup

1. Install ESP-IDF with **esp32p4** support.
2. Copy display/touch init from Elecrow’s ESP-IDF examples into [`components/crowpanel/crowpanel_board.c`](components/crowpanel/crowpanel_board.c) (marked `TODO`).
3. Configure WiFi and slideshow URL:

   ```bash
   idf.py menuconfig
   # Slideshow → Base URL (default http://pinky.local:8787)
   # Example Connection Configuration → WiFi
   ```

4. Build and flash:

   ```bash
   idf.py set-target esp32p4
   idf.py build flash monitor
   ```

## Features

- Polls `GET /api/v1/slideshow` on pinky
- 10 s auto-advance; tap pause; swipe when paused; pinch zoom on images
- I2S WAV for SVR/TOR alert changes (NVS dedupe)

## Audio assets

Place `svr.wav` and `tor.wav` under `main/assets/` and embed via `target_add_binary_data` in `main/CMakeLists.txt`, or fetch from pinky in a later revision.
