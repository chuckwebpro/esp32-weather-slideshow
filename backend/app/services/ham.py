from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET

import httpx

from app.config import settings
from app.models.slideshow import HamBandLine, HamSnapshot


async def fetch_ham(client: httpx.AsyncClient) -> tuple[HamSnapshot, str]:
    r = await client.get(settings.hamqsl_url, timeout=30.0)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    def text(path: str) -> str | None:
        el = root.find(path)
        return el.text.strip() if el is not None and el.text else None

    sfi = _int(text(".//solar/sfi"))
    k = _int(text(".//solar/kindex"))
    a = _int(text(".//solar/aindex"))

    bands: list[HamBandLine] = []
    for band_el in root.findall(".//band"):
        name = band_el.get("name") or "?"
        day = band_el.findtext("day") or band_el.findtext("daytext")
        night = band_el.findtext("night") or band_el.findtext("nighttext")
        bands.append(HamBandLine(band=name, day=day, night=night))

    summary_parts = []
    if sfi is not None:
        summary_parts.append(f"SFI {sfi}")
    if k is not None:
        summary_parts.append(f"K {k}")
    if a is not None:
        summary_parts.append(f"A {a}")

    snap = HamSnapshot(
        sfi=sfi,
        k_index=k,
        a_index=a,
        summary=", ".join(summary_parts) if summary_parts else None,
        bands=bands[:12],
    )
    revision = hashlib.sha256(r.content).hexdigest()[:12]
    return snap, revision


def _int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None
