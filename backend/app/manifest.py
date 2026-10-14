from datetime import datetime, timezone

from app.config import settings
from app.models.slideshow import (
    PlaybackMeta,
    SlideItem,
    SlideshowResponse,
)
from app.state import DataStore


def build_slideshow_response(store: DataStore) -> SlideshowResponse:
    base = f"/media"
    rev_radar_refl = store.get_revision("radar_reflectivity.jpg")
    rev_radar_vel = store.get_revision("radar_velocity.jpg")
    rev_outlook = store.get_revision("spc_day1_cat.jpg")

    slides: list[SlideItem] = [
        SlideItem(
            id="current_weather",
            type="weather",
            title="Current Weather",
            revision=store.get_revision("weather"),
        ),
        SlideItem(
            id="radar_reflectivity",
            type="image",
            title="Radar — Reflectivity",
            url=f"{base}/radar_reflectivity.jpg?r={rev_radar_refl}",
            revision=rev_radar_refl,
        ),
        SlideItem(
            id="radar_velocity",
            type="image",
            title="Radar — Velocity",
            url=f"{base}/radar_velocity.jpg?r={rev_radar_vel}",
            revision=rev_radar_vel,
        ),
        SlideItem(
            id="ham_band_conditions",
            type="ham",
            title="HF Band Conditions",
            revision=store.get_revision("ham"),
        ),
        SlideItem(
            id="spc_day1_cat",
            type="outlook",
            title="SPC Day 1 Outlook",
            url=f"{base}/spc_day1_cat.jpg?r={rev_outlook}",
            revision=rev_outlook,
        ),
    ]

    snap = store.snapshot()
    return SlideshowResponse(
        server_time=datetime.now(timezone.utc),
        refresh_after_sec=settings.refresh_after_sec,
        playback=PlaybackMeta(advance_sec=settings.playback_advance_sec, paused=False),
        slides=slides,
        weather=snap.weather,
        ham=snap.ham,
        alerts=snap.alerts,
    )
