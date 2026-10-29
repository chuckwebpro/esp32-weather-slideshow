from __future__ import annotations

import hashlib
import io
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

from app.config import settings
from app.render.counties import county_overlays, draw_county_land, draw_county_lines_and_names
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
    bbox: tuple[float, float, float, float] | None = None,
) -> str:
    width = settings.image_width
    height = settings.image_height
    if bbox is None:
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
        cropped = crop_ridge_image_to_bbox(
            src,
            bbox,
            center_lat=settings.ridge_site_lat,
            center_lon=settings.ridge_site_lon,
            range_km=settings.ridge_range_km,
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


def iem_reflectivity_url(
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> str:
    lon_w, lat_s, lon_e, lat_n = bbox
    return (
        f"{settings.iem_n0q_wms_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap"
        "&LAYERS=nexrad-n0q-900913&STYLES=&FORMAT=image/png&TRANSPARENT=TRUE"
        f"&SRS=EPSG:4326&BBOX={lon_w:.5f},{lat_s:.5f},{lon_e:.5f},{lat_n:.5f}"
        f"&WIDTH={width}&HEIGHT={height}"
    )


async def fetch_iem_reflectivity(
    client: httpx.AsyncClient,
    bbox: tuple[float, float, float, float],
) -> bytes:
    url = iem_reflectivity_url(bbox, settings.image_width, settings.image_height)
    r = await client.get(url, timeout=60.0)
    r.raise_for_status()
    if "image" not in r.headers.get("content-type", ""):
        raise ValueError(f"IEM radar was not an image ({r.headers.get('content-type')})")
    return r.content


def composite_iem_jpeg(
    png_bytes: bytes,
    alert_geojson: dict | None,
    out_path: Path,
    title: str,
    bbox: tuple[float, float, float, float],
) -> str:
    """Place a transparent N0Q render over county outlines at the panel size."""
    width = settings.image_width
    height = settings.image_height
    with Image.open(io.BytesIO(png_bytes)) as src:
        radar = src.convert("RGBA")
        if radar.size != (width, height):
            radar = radar.resize((width, height), Image.Resampling.LANCZOS)
    img = Image.new("RGB", (width, height), (8, 12, 20))
    overlays = county_overlays(bbox, width, height)
    base = ImageDraw.Draw(img)
    draw_county_land(base, overlays)
    img.paste(radar, (0, 0), radar)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_county_lines_and_names(draw, overlays)
    draw.rectangle((0, 0, width, 28), fill=(0, 0, 0, 160))
    draw.text((8, 6), title, fill=(255, 255, 255))
    if alert_geojson:
        _draw_alert_overlays(draw, alert_geojson, bbox, width, height)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=90)
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
