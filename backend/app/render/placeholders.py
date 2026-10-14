from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def ensure_placeholder_jpeg(
    path: Path,
    width: int,
    height: int,
    title: str,
    subtitle: str = "",
    rgb: tuple[int, int, int] = (32, 48, 64),
) -> None:
    if path.exists():
        return
    img = Image.new("RGB", (width, height), rgb)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((24, 24), title, fill=(240, 240, 240), font=font)
    if subtitle:
        draw.text((24, 48), subtitle, fill=(200, 200, 200), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="JPEG", quality=85)
