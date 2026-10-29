from pathlib import Path

from PIL import Image

from app.config import settings
from app.render.ridge_geo import crop_ridge_image_to_bbox


def test_fit_bbox_matches_panel_aspect():
    from app.render.ridge_geo import fit_bbox_to_aspect

    fitted = fit_bbox_to_aspect((-97.08, 32.78, -96.28, 33.82), width_px=1024, height_px=600)
    lon_w, lat_s, lon_e, lat_n = fitted
    lat_c = (lat_s + lat_n) / 2.0
    import math

    width_km = (lon_e - lon_w) * 111.32 * math.cos(math.radians(lat_c))
    height_km = (lat_n - lat_s) * 111.32
    assert abs(width_km / height_km - 1024 / 600) < 0.02
    # Center of the original box is preserved.
    assert abs(((lon_w + lon_e) / 2) - ((-97.08 + -96.28) / 2)) < 0.01
    assert abs(((lat_s + lat_n) / 2) - ((32.78 + 33.82) / 2)) < 0.01


def test_crop_ridge_produces_reasonable_size():
    gif = Path(__file__).resolve().parents[1] / "data" / "kfws0.gif"
    if not gif.is_file():
        return
    with Image.open(gif) as img:
        img = img.convert("RGB")
        cropped = crop_ridge_image_to_bbox(
            img,
            settings.radar_bbox,
            center_lat=settings.ridge_site_lat,
            center_lon=settings.ridge_site_lon,
            range_km=settings.ridge_range_km,
        )
    w, h = cropped.size
    assert 80 <= w <= 400
    assert 80 <= h <= 400
