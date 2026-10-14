from pathlib import Path

from PIL import Image

from app.config import settings
from app.render.ridge_geo import crop_ridge_image_to_bbox


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
