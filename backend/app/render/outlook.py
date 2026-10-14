from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw
from shapely.geometry import shape

from app.config import settings
from app.render.geo import polygon_to_pixel_ring

# CONUS extent for Day 1 cat layer
CONUS_BBOX = (-125.0, 24.0, -66.0, 50.0)

# SPC categorical risk fill colors (approximate standard)
RISK_COLORS = {
    "TSTM": (100, 200, 100, 140),
    "MRGL": (100, 180, 100, 160),
    "SLGT": (255, 255, 100, 180),
    "ENH": (255, 180, 100, 200),
    "MDT": (255, 100, 100, 210),
    "HIGH": (255, 0, 0, 220),
}


def _draw_states_basemap(
    draw: ImageDraw.ImageDraw,
    states_geojson: dict,
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> None:
    for feat in states_geojson.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            shp = shape(geom)
        except Exception:
            continue
        if shp.geom_type == "Polygon":
            parts = [shp]
        elif shp.geom_type == "MultiPolygon":
            parts = list(shp.geoms)
        else:
            continue
        for g in parts:
            ring = polygon_to_pixel_ring(g, bbox, width, height)
            if len(ring) >= 3:
                draw.polygon(ring, fill=(88, 98, 112, 255), outline=(200, 210, 220, 255))
                draw.line(ring + [ring[0]], fill=(220, 228, 235, 255), width=1)


def render_spc_outlook_jpeg(
    geojson: dict,
    out_path: Path,
    states_geojson: dict | None = None,
) -> str:
    width = settings.image_width
    height = settings.image_height
    bbox = CONUS_BBOX

    # Ocean background
    img = Image.new("RGBA", (width, height), (12, 22, 38, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    if states_geojson:
        _draw_states_basemap(draw, states_geojson, bbox, width, height)
    else:
        from app.services.basemap import load_us_states_bundled

        _draw_states_basemap(draw, load_us_states_bundled(), bbox, width, height)

    for feat in geojson.get("features", []):
        props = feat.get("properties") or {}
        label = (props.get("LABEL") or props.get("label") or "").upper()
        color = RISK_COLORS.get(label, (120, 120, 120, 100))
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            shp = shape(geom)
        except Exception:
            continue
        if shp.geom_type == "Polygon":
            ring = polygon_to_pixel_ring(shp, bbox, width, height)
            if len(ring) >= 3:
                draw.polygon(ring, fill=color, outline=(255, 255, 255, 100))
        elif shp.geom_type == "MultiPolygon":
            for part in shp.geoms:
                ring = polygon_to_pixel_ring(part, bbox, width, height)
                if len(ring) >= 3:
                    draw.polygon(ring, fill=color, outline=(255, 255, 255, 100))

    draw.rectangle((0, 0, width, 28), fill=(0, 0, 0, 180))
    draw.text((8, 6), "SPC Day 1 Categorical Outlook", fill=(255, 255, 255, 255))

    rgb = img.convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(out_path, format="JPEG", quality=88)
    return hashlib.sha256(out_path.read_bytes()).hexdigest()[:12]
