# ESP32-P4 Weather / Radar / HAM Slideshow — Pre-Planning Document

**Target hardware**  
- Display: Elecrow CrowPanel Advanced 10.1" ESP32-P4 (1024×600 MIPI-DSI, capacitive multi-touch GT911, 32 MB PSRAM, paired ESP32-C6 for Wi-Fi 6).  
- Backend: HP ProDesk 600 G6 (i5-10500T, 16 GB RAM) running TrueNAS SCALE.  

**Important constraint**  
All firmware is written for the **ESP32-P4** (ESP-IDF + LVGL). Do not reuse code or assumptions written for ESP32, ESP32-S3, or other variants.

**Overall architecture**  
TrueNAS performs all data fetching, parsing, image cropping, polygon overlay, and compositing. The ESP32-P4 only polls (or receives via MQTT), renders finished assets with LVGL, handles touch/gestures, and plays audio. Communication is local-network HTTP (baseline) or MQTT.

---

## 1. Slide List (Initial)

| Order | Slide | Content | Source |
|-------|-------|---------|--------|
| 1 | Current Weather | As much data as fits (temp, feels-like, humidity, wind, pressure, UV, conditions, sunrise/sunset, etc.) | Open-Meteo or NWS |
| 2 | Radar — Reflectivity | KFWS NEXRAD precip reflectivity, cropped to Collin Co., TX, with NWS warning polygons overlaid | NEXRAD + NWS alerts GeoJSON |
| 3 | Radar — Velocity | KFWS NEXRAD velocity, same crop and warning overlays | NEXRAD + NWS alerts GeoJSON |
| 4 | HAM Band Conditions | Current HF band conditions | HamQSL solar XML |
| 5 | Day 1 Convective Outlook | SPC Day 1 categorical outlook map (risk colors) | SPC `day1otlk_cat.lyr.geojson` |
| 6+ | Future | Home Assistant entities, additional slides | TrueNAS proxy to HA REST/MQTT |

Each radar product is on its **own dedicated slide**. Warning polygons are composited on TrueNAS so the P4 only displays finished JPEGs.

---

## 2. Interaction & Gesture Spec

- Auto-advance every **10 seconds** (LVGL timer).
- **Single tap** anywhere: toggle pause/resume.
- While paused:
  - Swipe left → next slide
  - Swipe right → previous slide
- Pinch (two-finger): zoom in/out on the current slide (primarily useful on radar and outlook images). Reset zoom to 1.0 on slide change or when resuming playback.
- Optional later: two-finger pan while zoomed.
- Visual feedback on pause (small status indicator that fades).
- Background data refresh continues even while paused so the next resume shows fresh content.

Enable `LV_USE_GESTURE_RECOGNITION` and feed multi-touch points from the GT911 into LVGL’s gesture recognizer.

---

## 3. Audio Alerts

- I2S output on the CrowPanel.
- Play short WAV clips for:
  - Severe Thunderstorm Warning
  - Tornado Warning
- Triggered when a relevant NWS alert appears or is updated in the local area.
- Volume and mute control can be added later; start with simple one-shot playback.

---

## 4. TrueNAS Backend Responsibilities

- Poll external sources on appropriate intervals.
- Crop radar to Collin County / KFWS coverage area of interest.
- Overlay NWS warning polygons (SVR / TOR) onto radar images using Pillow / GeoPandas or equivalent.
- Render convective outlook map with standard SPC risk colors.
- Serve:
  - JSON status endpoint(s) containing weather, HAM, alert metadata, HA entities (later), and image URLs or base64.
  - Pre-composited JPEG images (radar reflectivity, velocity, outlook).
- Cache results so the display never blocks on external APIs.
- Optional: MQTT topics for push updates (especially alerts).

Recommended stack on TrueNAS: Docker container running Python (FastAPI or Flask) + Pillow + relevant API clients.

---

## 5. ESP32-P4 Firmware Responsibilities

- ESP-IDF + LVGL (preferred over Arduino for this board).
- Full-screen or tabbed LVGL screens, one per slide.
- Image widgets that load JPEGs from the TrueNAS HTTP endpoints.
- Timer-driven slide advance with pause/resume.
- Gesture handling (tap, swipe, pinch) as specified above.
- I2S audio playback for alert clips.
- Periodic HTTP polling (or MQTT client) for updated JSON and images.
- Simple state machine: current slide index, paused flag, zoom level.

---

## 6. Data Sources (Reference)

- Weather: Open-Meteo or NWS points API (Collin County / nearby).
- Radar: KFWS NEXRAD (Dallas/Fort Worth site).
- Warnings: NWS alerts API (GeoJSON polygons).
- Convective Outlook: SPC Day 1 categorical GeoJSON.
- HAM: HamQSL solar XML.
- Future HA: Home Assistant REST API or MQTT (proxied through TrueNAS).

---

## 7. Suggested Build Order for Cursor / Composer

1. TrueNAS service skeleton: FastAPI endpoints that return static test JSON + placeholder images.
2. ESP32-P4 LVGL project: basic screen switching with 10 s timer and tap-to-pause.
3. Image loading from TrueNAS HTTP into LVGL image widgets.
4. Real weather JSON parsing and layout.
5. Radar image pipeline on TrueNAS (crop + overlay) and dedicated radar slides.
6. Swipe navigation while paused.
7. HAM and Convective Outlook slides.
8. Audio alert playback.
9. Pinch zoom on image slides.
10. Home Assistant proxy and slide (later).

---

## 8. Notes for Implementation

- Keep the ESP32-P4 as lightweight as possible; all image work stays on TrueNAS.
- Use JPEG for images to limit bandwidth and memory.
- Design the JSON schema to be easily extensible for future slides.
- Local-only operation; no cloud dependency required at runtime once data is cached.
- Document pinouts and display/touch init from Elecrow’s ESP-IDF examples for the exact board.

This document is ready to paste into Cursor as the project brief for Composer.