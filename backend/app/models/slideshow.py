from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SlideType = Literal["weather", "image", "ham", "outlook", "ha"]


class PlaybackMeta(BaseModel):
    advance_sec: int = 10
    paused: bool = False


class SlideItem(BaseModel):
    id: str
    type: SlideType
    title: str
    url: str | None = None
    revision: str


class ForecastDay(BaseModel):
    day_label: str
    date_label: str
    conditions: str
    high_f: float | None = None
    low_f: float | None = None
    precip_pct: int | None = None
    weather_code: int | None = None


class WeatherSnapshot(BaseModel):
    temperature_f: float | None = None
    feels_like_f: float | None = None
    humidity_pct: float | None = None
    wind_mph: float | None = None
    wind_direction: str | None = None
    pressure_inhg: float | None = None
    uv_index: float | None = None
    conditions: str | None = None
    weather_code: int | None = None
    sunrise: str | None = None
    sunset: str | None = None


class HamBandLine(BaseModel):
    band: str
    day: str | None = None
    night: str | None = None


class HamSnapshot(BaseModel):
    sfi: int | None = None
    k_index: int | None = None
    a_index: int | None = None
    summary: str | None = None
    bands: list[HamBandLine] = Field(default_factory=list)


class AlertItem(BaseModel):
    id: str
    event: str
    updated: datetime
    headline: str | None = None


class SlideshowResponse(BaseModel):
    server_time: datetime
    refresh_after_sec: int
    playback: PlaybackMeta
    slides: list[SlideItem]
    weather: WeatherSnapshot | None = None
    forecast: list[ForecastDay] = Field(default_factory=list)
    ham: HamSnapshot | None = None
    alerts: list[AlertItem] = Field(default_factory=list)
