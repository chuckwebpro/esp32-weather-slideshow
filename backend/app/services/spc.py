from __future__ import annotations

import hashlib

import httpx

from app.config import settings


async def fetch_spc_geojson(client: httpx.AsyncClient) -> tuple[dict, str]:
    r = await client.get(settings.spc_day1_cat_url, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    revision = hashlib.sha256(r.content).hexdigest()[:12]
    return data, revision
