from __future__ import annotations

import hashlib
from datetime import date, datetime

import httpx

from app.config import settings
from app.models.slideshow import ForecastDay, WeatherSnapshot


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


async def fetch_forecast(client: httpx.AsyncClient) -> tuple[list[ForecastDay], str]:
    params = {
        "latitude": settings.slideshow_lat,
        "longitude": settings.slideshow_lon,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ],
        "timezone": settings.timezone,
        "forecast_days": 7,
    }
    r = await client.get(settings.open_meteo_url, params=params, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    daily = data.get("daily", {})
    dates = daily.get("time") or []
    codes = daily.get("weather_code") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []
    pops = daily.get("precipitation_probability_max") or []

    days: list[ForecastDay] = []
    for i, iso in enumerate(dates[:7]):
        try:
            d = date.fromisoformat(iso)
        except ValueError:
            continue
        code = codes[i] if i < len(codes) else None
        high = highs[i] if i < len(highs) else None
        low = lows[i] if i < len(lows) else None
        pop = pops[i] if i < len(pops) else None
        days.append(
            ForecastDay(
                day_label="Today" if i == 0 else d.strftime("%a"),
                date_label=f"{d.strftime('%b')} {d.day}",
                conditions=_forecast_condition(code),
                high_f=_c_to_f(high),
                low_f=_c_to_f(low),
                precip_pct=None if pop is None else int(round(pop)),
                weather_code=code,
            )
        )
    revision = hashlib.sha256(r.content).hexdigest()[:12]
    return days, revision


def _forecast_condition(code: int | None) -> str:
    if code is None:
        return "Unknown"
    table = {
        0: "Clear",
        1: "Mostly clear",
        2: "Partly cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Drizzle",
        56: "Freezing drizzle",
        57: "Freezing drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        66: "Freezing rain",
        67: "Freezing rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        77: "Snow",
        80: "Showers",
        81: "Showers",
        82: "Heavy showers",
        85: "Snow showers",
        86: "Snow showers",
        95: "Storms",
        96: "Storms, hail",
        99: "Storms, hail",
    }
    return table.get(code, "Mixed")


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
