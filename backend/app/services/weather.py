from __future__ import annotations

import hashlib
from datetime import datetime

import httpx

from app.config import settings
from app.models.slideshow import WeatherSnapshot


def _c_to_f(c: float | None) -> float | None:
    if c is None:
        return None
    return c * 9 / 5 + 32


def _hpa_to_inhg(hpa: float | None) -> float | None:
    if hpa is None:
        return None
    return round(hpa * 0.02953, 2)


def _kmh_to_mph(kmh: float | None) -> float | None:
    if kmh is None:
        return None
    return round(kmh * 0.621371, 1)


def _wmo_to_cardinal(deg: float | None) -> str | None:
    if deg is None:
        return None
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((deg + 22.5) / 45) % 8]


async def fetch_weather(client: httpx.AsyncClient) -> tuple[WeatherSnapshot, str]:
    params = {
        "latitude": settings.slideshow_lat,
        "longitude": settings.slideshow_lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "uv_index",
            "weather_code",
        ],
        "daily": ["sunrise", "sunset", "weather_code"],
        "timezone": settings.timezone,
        "forecast_days": 1,
    }
    r = await client.get(settings.open_meteo_url, params=params, timeout=30.0)
    r.raise_for_status()
    data = r.json()

    current = data.get("current", {})
    daily = data.get("daily", {})
    code = current.get("weather_code")
    conditions = _weather_code_text(code)

    sunrise_raw = (daily.get("sunrise") or [None])[0]
    sunset_raw = (daily.get("sunset") or [None])[0]

    snap = WeatherSnapshot(
        temperature_f=_c_to_f(current.get("temperature_2m")),
        feels_like_f=_c_to_f(current.get("apparent_temperature")),
        humidity_pct=current.get("relative_humidity_2m"),
        wind_mph=_kmh_to_mph(current.get("wind_speed_10m")),
        wind_direction=_wmo_to_cardinal(current.get("wind_direction_10m")),
        pressure_inhg=_hpa_to_inhg(current.get("surface_pressure")),
        uv_index=current.get("uv_index"),
        conditions=conditions,
        sunrise=_format_local_time(sunrise_raw),
        sunset=_format_local_time(sunset_raw),
    )
    revision = hashlib.sha256(r.content).hexdigest()[:12]
    return snap, revision


def _format_local_time(iso: str | None) -> str | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        t = dt.strftime("%I:%M %p")
        return t.lstrip("0") if t.startswith("0") else t
    except ValueError:
        return iso


def _weather_code_text(code: int | None) -> str | None:
    if code is None:
        return None
    table = {
        0: "Clear",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Dense drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return table.get(code, f"Code {code}")
