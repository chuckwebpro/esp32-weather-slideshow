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

    sol = root.find(".//solardata") or root

    def text(tag: str) -> str | None:
        el = sol.find(tag)
        if el is not None and el.text:
            return el.text.strip()
        return None

    sfi = _int(text("solarflux"))
    k = _int(text("kindex"))
    a = _int(text("aindex"))

    bands: list[HamBandLine] = []
    calc = sol.find("calculatedconditions")
    if calc is not None:
        by_name: dict[str, HamBandLine] = {}
        for band_el in calc.findall("band"):
            name = band_el.get("name") or "?"
            when = band_el.get("time") or "day"
            cond = (band_el.text or "").strip()
            line = by_name.setdefault(name, HamBandLine(band=name))
            if when == "night":
                line.night = cond
            else:
                line.day = cond
        bands = list(by_name.values())

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
