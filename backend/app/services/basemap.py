from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CACHE_NAME = "us_states.json"
CACHE_MAX_AGE_SEC = 7 * 24 * 3600


def _cache_path(data_dir: Path) -> Path:
    return data_dir / "cache" / CACHE_NAME


def load_us_states_cache(data_dir: Path) -> dict | None:
    path = _cache_path(data_dir)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


async def fetch_us_states_geojson(client: httpx.AsyncClient, data_dir: Path) -> dict:
    path = _cache_path(data_dir)
    if path.is_file():
        age = datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
        if age < CACHE_MAX_AGE_SEC:
            cached = load_us_states_cache(data_dir)
            if cached:
                return cached

    r = await client.get(settings.us_states_geojson_url, timeout=60.0)
    r.raise_for_status()
    data = r.json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    logger.info("Cached US states GeoJSON for SPC basemap")
    return data
