from __future__ import annotations

import hashlib
import io
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

from app.config import settings
from app.render.geo import feature_collection_to_shapes, merge_polygons, polygon_to_pixel_ring
from app.render.ridge_geo import crop_ridge_image_to_bbox


async def fetch_ridge_gif(client: httpx.AsyncClient, url: str) -> bytes:
    r = await client.get(url, timeout=60.0)
    r.raise_for_status()
    return r.content


def composite_radar_jpeg(
    gif_bytes: bytes,
    alert_geojson: dict | None,
    out_path: Path,
    title: str,
) -> str:
    width = settings.image_width
    height = settings.image_height
    bbox = settings.radar_bbox
    if settings.ridge_offset_km_east or settings.ridge_offset_km_north:
        from app.render.ridge_geo import shift_bbox_km

        bbox = shift_bbox_km(
            bbox,
            settings.ridge_offset_km_east,
            settings.ridge_offset_km_north,
        )

    with Image.open(io.BytesIO(gif_bytes)) as src:
        src = src.convert("RGB")
        crop_bbox = settings.radar_bbox
        cropped = crop_ridge_image_to_bbox(
            src,
            crop_bbox,
            center_lat=settings.ridge_site_lat,
            center_lon=settings.ridge_site_lon,
            range_km=settings.ridge_range_km,
            offset_km_east=settings.ridge_offset_km_east,
            offset_km_north=settings.ridge_offset_km_north,
        )
        img = cropped.resize((width, height), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle((0, 0, width, 28), fill=(0, 0, 0, 160))
    draw.text((8, 6), title, fill=(255, 255, 255))

    if alert_geojson:
        _draw_alert_overlays(draw, alert_geojson, bbox, width, height)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=88)
    return hashlib.sha256(out_path.read_bytes()).hexdigest()[:12]


def _draw_alert_overlays(
    draw: ImageDraw.ImageDraw,
    geojson: dict,
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> None:
    shapes = feature_collection_to_shapes(geojson)
    merged = merge_polygons(shapes)
    if merged is None:
        return

    geoms = [merged] if merged.geom_type != "GeometryCollection" else merged.geoms
    for geom in geoms:
        if geom.geom_type == "Polygon":
            ring = polygon_to_pixel_ring(geom, bbox, width, height)
            if len(ring) >= 3:
                draw.polygon(ring, outline=(255, 64, 64, 220), fill=(255, 0, 0, 60))
        elif geom.geom_type == "MultiPolygon":
            for part in geom.geoms:
                ring = polygon_to_pixel_ring(part, bbox, width, height)
                if len(ring) >= 3:
                    draw.polygon(ring, outline=(255, 64, 64, 220), fill=(255, 0, 0, 60))
