from __future__ import annotations

import math

from PIL import Image


def latlon_to_ridge_pixel(
    lat: float,
    lon: float,
    *,
    center_lat: float,
    center_lon: float,
    range_km: float,
    width: int,
    height: int,
) -> tuple[float, float]:
    """Map lat/lon to pixel on NOAA Ridge standard azimuthal-equidistant-style GIF."""
    earth_km = 6371.0
    phi1 = math.radians(center_lat)
    phi2 = math.radians(lat)
    dlam = math.radians(lon - center_lon)

    cos_c = (
        math.sin(phi1) * math.sin(phi2)
        + math.cos(phi1) * math.cos(phi2) * math.cos(dlam)
    )
    cos_c = max(-1.0, min(1.0, cos_c))
    dist_km = earth_km * math.acos(cos_c)
    if dist_km < 1e-6:
        return width / 2.0, height / 2.0

    bearing = math.atan2(
        math.sin(dlam) * math.cos(phi2),
        math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam),
    )
    x_km = dist_km * math.sin(bearing)
    y_km = dist_km * math.cos(bearing)

    scale = (min(width, height) / 2.0) / range_km
    px = width / 2.0 + x_km * scale
    py = height / 2.0 - y_km * scale
    return px, py


def shift_bbox_km(
    bbox: tuple[float, float, float, float],
    km_east: float,
    km_north: float,
) -> tuple[float, float, float, float]:
    lon_w, lat_s, lon_e, lat_n = bbox
    lat_c = (lat_s + lat_n) / 2.0
    dlon = km_east / (111.32 * math.cos(math.radians(lat_c)))
    dlat = km_north / 111.32
    return (lon_w + dlon, lat_s + dlat, lon_e + dlon, lat_n + dlat)


def fit_bbox_to_aspect(
    bbox: tuple[float, float, float, float],
    *,
    width_px: int,
    height_px: int,
) -> tuple[float, float, float, float]:
    """Expand a lat/lon box, around its center, to the screen's aspect ratio.

    A tall county box forced into a 1024×600 frame gets stretched sideways.
    Growing the shorter side keeps shapes square and uses more of the source.
    """
    lon_w, lat_s, lon_e, lat_n = bbox
    lat_c = (lat_s + lat_n) / 2.0
    km_per_lat = 111.32
    km_per_lon = 111.32 * math.cos(math.radians(lat_c))
    width_km = max((lon_e - lon_w) * km_per_lon, 1.0)
    height_km = max((lat_n - lat_s) * km_per_lat, 1.0)
    target = width_px / height_px
    aspect = width_km / height_km
    if aspect < target:
        width_km = height_km * target
        half = (width_km / km_per_lon) / 2.0
        mid = (lon_w + lon_e) / 2.0
        lon_w, lon_e = mid - half, mid + half
    elif aspect > target:
        height_km = width_km / target
        half = (height_km / km_per_lat) / 2.0
        mid = (lat_s + lat_n) / 2.0
        lat_s, lat_n = mid - half, mid + half
    return (lon_w, lat_s, lon_e, lat_n)


def display_radar_bbox() -> tuple[float, float, float, float]:
    """BBox after the Ridge nudge, shaped for the panel."""
    from app.config import settings

    bbox = settings.radar_bbox
    if settings.ridge_offset_km_east or settings.ridge_offset_km_north:
        bbox = shift_bbox_km(
            bbox,
            settings.ridge_offset_km_east,
            settings.ridge_offset_km_north,
        )
    return fit_bbox_to_aspect(
        bbox,
        width_px=settings.image_width,
        height_px=settings.image_height,
    )


def crop_ridge_image_to_bbox(
    img: Image.Image,
    bbox: tuple[float, float, float, float],
    *,
    center_lat: float,
    center_lon: float,
    range_km: float,
    offset_km_east: float = 0.0,
    offset_km_north: float = 0.0,
) -> Image.Image:
    """Crop Ridge GIF to geographic bbox (lon_w, lat_s, lon_e, lat_n)."""
    if offset_km_east or offset_km_north:
        bbox = shift_bbox_km(bbox, offset_km_east, offset_km_north)
    lon_w, lat_s, lon_e, lat_n = bbox
    w, h = img.size

    corners = (
        (lat_s, lon_w),
        (lat_s, lon_e),
        (lat_n, lon_w),
        (lat_n, lon_e),
    )
    xs: list[float] = []
    ys: list[float] = []
    for lat, lon in corners:
        x, y = latlon_to_ridge_pixel(
            lat,
            lon,
            center_lat=center_lat,
            center_lon=center_lon,
            range_km=range_km,
            width=w,
            height=h,
        )
        xs.append(x)
        ys.append(y)

    pad = 4
    left = max(0, int(min(xs)) - pad)
    right = min(w, int(max(xs)) + pad)
    top = max(0, int(min(ys)) - pad)
    bottom = min(h, int(max(ys)) + pad)

    if right - left < 32 or bottom - top < 32:
        # Fallback if projection calibration is off
        left = int(w * 0.42)
        top = int(h * 0.08)
        right = int(w * 0.88)
        bottom = int(h * 0.52)

    return img.crop((left, top, right, bottom))
