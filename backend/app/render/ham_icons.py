from __future__ import annotations

import math

from PIL import Image, ImageDraw

_SUN = (242, 184, 75, 255)
_MOON = (232, 236, 244, 255)
_WAVE = (186, 196, 208, 255)
_DIM = (72, 76, 84, 255)


def _canvas(size: int, scale: int = 4) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    side = size * scale
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image), side


def sun_icon(size: int = 28) -> Image.Image:
    image, draw, side = _canvas(size)
    cx = cy = side / 2
    radius = side * 0.18
    width = max(4, int(radius * 0.32))
    for i in range(8):
        angle = math.radians(i * 45)
        draw.line(
            (
                cx + math.cos(angle) * radius * 1.55,
                cy + math.sin(angle) * radius * 1.55,
                cx + math.cos(angle) * radius * 2.35,
                cy + math.sin(angle) * radius * 2.35,
            ),
            fill=_SUN,
            width=width,
        )
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_SUN)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def moon_icon(size: int = 28) -> Image.Image:
    image, draw, side = _canvas(size)
    pad = side * 0.16
    draw.ellipse((pad, pad, side - pad, side - pad), fill=_MOON)
    shift = side * 0.30
    draw.ellipse(
        (pad + shift, pad - side * 0.06, side - pad + shift, side - pad - side * 0.02),
        fill=(0, 0, 0, 0),
    )
    return image.resize((size, size), Image.Resampling.LANCZOS)


def wave_icon(size: int = 30) -> Image.Image:
    image, draw, side = _canvas(size)
    cx = side * 0.22
    cy = side * 0.50
    stroke = max(4, side // 18)
    for radius in (side * 0.22, side * 0.40, side * 0.58):
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        draw.arc(box, start=310, end=50, fill=_WAVE, width=stroke)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def signal_meter(level: int, color: tuple[int, int, int], size: int = 34) -> Image.Image:
    """Three bars. level 1–3 lights that many from the left."""
    scale = 4
    width = size * scale
    height = int(size * 0.85) * scale
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    gap = width * 0.10
    bar_w = (width - gap * 4) / 3
    lit = (*color, 255)
    for i, frac in enumerate((0.42, 0.70, 1.0)):
        bar_h = (height - gap) * frac
        x = gap + i * (bar_w + gap)
        y = height - gap - bar_h
        fill = lit if i < level else _DIM
        draw.rounded_rectangle((x, y, x + bar_w, height - gap * 0.4), radius=bar_w * 0.35, fill=fill)
    return image.resize((size, int(size * 0.85)), Image.Resampling.LANCZOS)


def signal_level(value: str | None) -> int:
    word = (value or "").strip().lower()
    if word == "good":
        return 3
    if word == "fair":
        return 2
    if word == "poor":
        return 1
    return 0
