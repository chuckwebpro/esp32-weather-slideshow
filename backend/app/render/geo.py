from __future__ import annotations

from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


def feature_collection_to_shapes(geojson: dict) -> list[Any]:
    shapes = []
    for feat in geojson.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            shapes.append(shape(geom))
        except Exception:
            continue
    return shapes


def merge_polygons(shapes: list[Any]) -> Any | None:
    if not shapes:
        return None
    return unary_union(shapes)


def polygon_to_pixel_ring(
    poly: Any,
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> list[tuple[float, float]]:
    lon_w, lat_s, lon_e, lat_n = bbox

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - lon_w) / (lon_e - lon_w) * width
        y = (lat_n - lat) / (lat_n - lat_s) * height
        return x, y

    coords = mapping(poly).get("coordinates", [])
    if not coords:
        return []

    ring = coords[0] if poly.geom_type == "Polygon" else coords[0][0]
    return [project(lon, lat) for lon, lat in ring]
