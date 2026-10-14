from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw

from app.config import settings
from app.render.geo import polygon_to_pixel_ring

# SPC categorical risk fill colors (approximate standard)
RISK_COLORS = {
    "TSTM": (100, 200, 100, 100),
    "MRGL": (100, 180, 100, 120),
    "SLGT": (255, 255, 100, 140),
    "ENH": (255, 180, 100, 160),
    "MDT": (255, 100, 100, 180),
    "HIGH": (255, 0, 0, 200),
}


def render_spc_outlook_jpeg(geojson: dict, out_path: Path) -> str:
    width = settings.image_width
    height = settings.image_height
    # CONUS Day 1 cat layer — use full extent
    bbox = (-125.0, 24.0, -66.0, 50.0)

    img = Image.new("RGB", (width, height), (24, 32, 48))
    draw = ImageDraw.Draw(img, "RGBA")

    for feat in geojson.get("features", []):
        props = feat.get("properties") or {}
        label = (props.get("LABEL") or props.get("label") or "").upper()
        color = RISK_COLORS.get(label, (120, 120, 120, 80))
        geom = feat.get("geometry")
        if not geom:
            continue
        from shapely.geometry import shape

        try:
            shp = shape(geom)
        except Exception:
            continue
        if shp.geom_type == "Polygon":
            ring = polygon_to_pixel_ring(shp, bbox, width, height)
            if len(ring) >= 3:
                draw.polygon(ring, fill=color, outline=(255, 255, 255, 80))
        elif shp.geom_type == "MultiPolygon":
            for part in shp.geoms:
                ring = polygon_to_pixel_ring(part, bbox, width, height)
                if len(ring) >= 3:
                    draw.polygon(ring, fill=color, outline=(255, 255, 255, 80))

    draw.rectangle((0, 0, width, 28), fill=(0, 0, 0, 160))
    draw.text((8, 6), "SPC Day 1 Categorical Outlook", fill=(255, 255, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=88)
    return hashlib.sha256(out_path.read_bytes()).hexdigest()[:12]
