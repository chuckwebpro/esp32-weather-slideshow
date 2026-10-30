# Slideshow API v1

Base URL on pinky: `http://pinky.local:8787`

## `GET /health`

```json
{
  "status": "ok",
  "last_refresh": "2026-03-22T12:00:00+00:00"
}
```

## `GET /api/v1/slideshow`

Primary poll endpoint for **brain.local**.

| Field | Type | Description |
|-------|------|-------------|
| `server_time` | ISO-8601 UTC | Server clock |
| `refresh_after_sec` | int | Suggested client poll interval (default 45) |
| `playback.advance_sec` | int | Auto-advance interval (default 10); pause is local on device |
| `playback.paused` | bool | Informational; firmware owns pause state |
| `slides` | array | Ordered slide list |
| `weather` | object | Current conditions for weather slide |
| `ham` | object | HF band conditions |
| `alerts` | array | Active NWS warnings (SVR/TOR drive audio) |

### Slide object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier (see below) |
| `type` | string | `weather`, `image`, `ham`, `outlook`, `ha` (future) |
| `title` | string | Display title |
| `url` | string? | Relative JPEG URL for `image` / `outlook` |
| `revision` | string | Cache-bust token |

### Slide IDs (initial order)

1. `current_weather` — type `weather`
2. `forecast_7day` — type `image` (rendered JPEG)
3. `radar_reflectivity` — type `image`
4. `radar_velocity` — type `image`
5. `ham_band_conditions` — type `ham`
6. `spc_day1_cat` — type `outlook`

### Weather object

`temperature_f`, `feels_like_f`, `humidity_pct`, `wind_mph`, `wind_direction`, `pressure_inhg`, `uv_index`, `conditions`, `sunrise`, `sunset`

### Forecast

`forecast` is a list of seven days used to draw `forecast_7day.jpg`. Each day has `day_label`, `date_label`, `conditions`, `high_f`, `low_f`, `precip_pct`, and `weather_code`. The panel shows the JPEG, not this object.

### HAM object

`sfi`, `k_index`, `a_index`, `summary`, `bands[]` with `band`, `day`, `night`

### Alert object

`id`, `event`, `updated`, `headline` — firmware compares `id` + `updated` against NVS to play WAV once per new/updated SVR/TOR.

## `GET /media/{filename}.jpg`

Pre-composited JPEGs at **1024×600**. Query `?r=` from slide `url` is optional cache buster.

Files:

- `forecast_7day.jpg`
- `radar_reflectivity.jpg`
- `radar_velocity.jpg`
- `spc_day1_cat.jpg`

## Example

```json
{
  "server_time": "2026-03-22T18:00:00Z",
  "refresh_after_sec": 45,
  "playback": { "advance_sec": 10, "paused": false },
  "slides": [
    {
      "id": "current_weather",
      "type": "weather",
      "title": "Current Weather",
      "url": null,
      "revision": "a1b2c3d4e5f6"
    },
    {
      "id": "radar_reflectivity",
      "type": "image",
      "title": "Radar — Reflectivity",
      "url": "/media/radar_reflectivity.jpg?r=abc123",
      "revision": "abc123"
    }
  ],
  "weather": {
    "temperature_f": 72.5,
    "conditions": "Partly cloudy"
  },
  "ham": { "sfi": 120, "k_index": 2, "bands": [] },
  "alerts": []
}
```
