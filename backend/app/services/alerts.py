from __future__ import annotations

from datetime import datetime

import httpx

from app.config import settings
from app.models.slideshow import AlertItem

AUDIO_EVENTS = {"Severe Thunderstorm Warning", "Tornado Warning"}


def parse_alerts_geojson(payload: dict) -> list[AlertItem]:
    features = payload.get("features", [])
    alerts: list[AlertItem] = []
    for feat in features:
        props = feat.get("properties") or {}
        event = props.get("event") or ""
        if event not in AUDIO_EVENTS and "Warning" not in event:
            continue
        alert_id = props.get("id") or feat.get("id") or ""
        updated_raw = props.get("sent") or props.get("effective") or props.get("updated")
        updated = _parse_dt(updated_raw)
        alerts.append(
            AlertItem(
                id=str(alert_id),
                event=event,
                updated=updated,
                headline=props.get("headline"),
            )
        )
    alerts.sort(key=lambda a: a.updated, reverse=True)
    return alerts


async def fetch_alerts_geojson(client: httpx.AsyncClient) -> dict:
    point_url = (
        f"https://api.weather.gov/alerts/active?"
        f"point={settings.slideshow_lat},{settings.slideshow_lon}"
    )
    headers = {"User-Agent": settings.nws_user_agent, "Accept": "application/geo+json"}
    r = await client.get(point_url, headers=headers, timeout=30.0)
    r.raise_for_status()
    return r.json()


async def fetch_alerts(client: httpx.AsyncClient) -> list[AlertItem]:
    geo = await fetch_alerts_geojson(client)
    return parse_alerts_geojson(geo)


def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.utcnow()
