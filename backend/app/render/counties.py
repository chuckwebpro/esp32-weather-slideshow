from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box, shape

from app.render.geo import polygon_to_pixel_ring

_BUNDLED = Path(__file__).resolve().parent.parent / "assets" / "us_counties.geojson"
_SHAPES: list[tuple[Any, str]] | None = None

FILL = (28, 40, 58)
OUTLINE = (210, 220, 230)
LABEL = (245, 245, 245, 230)
LABEL_SHADOW = (0, 0, 0, 200)


def _county_shapes() -> list[tuple[Any, str]]:
    global _SHAPES
    if _SHAPES is not None:
        return _SHAPES
    data = json.loads(_BUNDLED.read_text(encoding="utf-8"))
    prepared: list[tuple[Any, str]] = []
    for feat in data.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        name = str((feat.get("properties") or {}).get("NAME") or "")
        try:
            prepared.append((shape(geom), name))
        except Exception:
            continue
    _SHAPES = prepared
    return prepared


def _parts(geom: Any) -> list[Any]:
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type == "MultiPolygon":
        return list(geom.geoms)
    return []


def _main_polygon(geom: Any) -> Any | None:
    if geom.is_empty:
        return None
    if geom.geom_type == "Polygon":
        return geom
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    if geom.geom_type == "GeometryCollection":
        found = [p for g in geom.geoms if (p := _main_polygon(g)) is not None]
        return max(found, key=lambda g: g.area) if found else None
    return None


def _project(
    lon: float,
    lat: float,
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[float, float]:
    lon_w, lat_s, lon_e, lat_n = bbox
    x = (lon - lon_w) / (lon_e - lon_w) * width
    y = (lat_n - lat) / (lat_n - lat_s) * height
    return x, y


def county_overlays(
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> list[tuple[list[list[tuple[float, float]]], tuple[str, float, float] | None]]:
    """County rings and an optional name, for counties that meet the view."""
    lon_w, lat_s, lon_e, lat_n = bbox
    view = box(lon_w, lat_s, lon_e, lat_n)
    overlays: list[tuple[list[list[tuple[float, float]]], tuple[str, float, float] | None]] = []
    for shp, name in _county_shapes():
        minx, miny, maxx, maxy = shp.bounds
        if maxx < lon_w or minx > lon_e or maxy < lat_s or miny > lat_n:
            continue
        if not shp.intersects(view):
            continue
        rings: list[list[tuple[float, float]]] = []
        for part in _parts(shp):
            if not part.intersects(view):
                continue
            ring = polygon_to_pixel_ring(part, bbox, width, height)
            if len(ring) >= 3:
                rings.append(ring)
        if not rings:
            continue
        label = None
        visible = _main_polygon(shp.intersection(view))
        if visible is not None and name:
            vx0, vy0, vx1, vy1 = visible.bounds
            px_w = (vx1 - vx0) / (lon_e - lon_w) * width
            px_h = (vy1 - vy0) / (lat_n - lat_s) * height
            if px_w >= 72 and px_h >= 40:
                pt = visible.representative_point()
                x, y = _project(pt.x, pt.y, bbox, width, height)
                if 8 < x < width - 8 and 36 < y < height - 8:
                    label = (name, x, y)
        overlays.append((rings, label))
    return overlays


def draw_county_land(
    draw: ImageDraw.ImageDraw,
    overlays: list[tuple[list[list[tuple[float, float]]], tuple[str, float, float] | None]],
) -> None:
    for rings, _label in overlays:
        for ring in rings:
            draw.polygon(ring, fill=FILL)


def draw_county_lines_and_names(
    draw: ImageDraw.ImageDraw,
    overlays: list[tuple[list[list[tuple[float, float]]], tuple[str, float, float] | None]],
) -> None:
    font = ImageFont.load_default(size=22)
    for rings, label in overlays:
        for ring in rings:
            draw.line(ring + [ring[0]], fill=OUTLINE, width=2)
        if label is None:
            continue
        name, x, y = label
        draw.text((x + 1, y + 1), name, fill=LABEL_SHADOW, anchor="mm", font=font)
        draw.text((x, y), name, fill=LABEL, anchor="mm", font=font)
