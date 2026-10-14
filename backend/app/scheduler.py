from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.render.outlook import render_spc_outlook_jpeg
from app.render.placeholders import ensure_placeholder_jpeg
from app.render.radar import composite_radar_jpeg, fetch_ridge_gif
from app.services.alerts import fetch_alerts_geojson, parse_alerts_geojson
from app.services.ham import fetch_ham
from app.services.basemap import fetch_us_states_geojson
from app.services.spc import fetch_spc_geojson
from app.services.weather import fetch_weather
from app.state import DataStore

logger = logging.getLogger(__name__)


async def refresh_all(store: DataStore) -> None:
    logger.info("Starting refresh cycle")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await _refresh_weather(store, client)
        alerts_geo = await _refresh_alerts(store, client)
        await _refresh_ham(store, client)
        await _refresh_spc(store, client)
        await _refresh_radar(store, client, alerts_geo)
    with store._lock:
        store.state.last_refresh = datetime.now(timezone.utc)
    logger.info("Refresh cycle complete")


async def _refresh_weather(store: DataStore, client: httpx.AsyncClient) -> None:
    try:
        snap, rev = await fetch_weather(client)
        with store._lock:
            store.state.weather = snap
        store.set_revision("weather", rev)
        store.save_json_cache("weather", snap.model_dump())
    except Exception:
        logger.exception("Weather refresh failed")


async def _refresh_alerts(store: DataStore, client: httpx.AsyncClient) -> dict | None:
    try:
        geo = await fetch_alerts_geojson(client)
        alerts = parse_alerts_geojson(geo)
        with store._lock:
            store.state.alerts = alerts
        store.save_json_cache("alerts", [a.model_dump(mode="json") for a in alerts])
        return geo
    except Exception:
        logger.exception("Alerts refresh failed")
        return None


async def _refresh_ham(store: DataStore, client: httpx.AsyncClient) -> None:
    try:
        snap, rev = await fetch_ham(client)
        with store._lock:
            store.state.ham = snap
        store.set_revision("ham", rev)
        store.save_json_cache("ham", snap.model_dump())
    except Exception:
        logger.exception("HAM refresh failed")


async def _refresh_spc(store: DataStore, client: httpx.AsyncClient) -> None:
    try:
        geojson, rev = await fetch_spc_geojson(client)
        states = await fetch_us_states_geojson(client, store.data_dir)
        out = store.media_path("spc_day1_cat.jpg")
        file_rev = render_spc_outlook_jpeg(geojson, out, states_geojson=states)
        store.set_revision("spc_day1_cat.jpg", file_rev or rev)
    except Exception:
        logger.exception("SPC refresh failed")


async def _refresh_radar(
    store: DataStore,
    client: httpx.AsyncClient,
    alerts_geo: dict | None,
) -> None:
    for url, name, title in (
        (settings.ridge_reflectivity_url, "radar_reflectivity.jpg", "KFWS Reflectivity"),
        (settings.ridge_velocity_url, "radar_velocity.jpg", "KFWS Velocity"),
    ):
        try:
            gif = await fetch_ridge_gif(client, url)
            out = store.media_path(name)
            rev = composite_radar_jpeg(gif, alerts_geo, out, title)
            store.set_revision(name, rev)
        except Exception:
            logger.exception("Radar refresh failed for %s", name)


def ensure_bootstrap_media(store: DataStore) -> None:
    w, h = settings.image_width, settings.image_height
    for name, title in (
        ("radar_reflectivity.jpg", "Radar Reflectivity (placeholder)"),
        ("radar_velocity.jpg", "Radar Velocity (placeholder)"),
        ("spc_day1_cat.jpg", "SPC Outlook (placeholder)"),
    ):
        ensure_placeholder_jpeg(store.media_path(name), w, h, title)


def start_scheduler(store: DataStore) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_all, "interval", minutes=3, args=[store], id="refresh_all")
    return scheduler
