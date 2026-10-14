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
