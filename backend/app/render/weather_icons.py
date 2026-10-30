from __future__ import annotations

import math

from PIL import Image, ImageDraw

_SUN = (242, 184, 75, 255)
_CLOUD = (226, 232, 238, 255)
_RAIN = (138, 180, 248, 255)
_SNOW = (236, 244, 252, 255)
_BOLT = (255, 214, 92, 255)
_FOG = (186, 196, 208, 255)


def weather_icon(code: int | None, size: int = 68) -> Image.Image:
    """Anti-aliased weather glyph for a WMO weather code."""
    scale = 4
    canvas = size * scale
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    kind = _kind(code)
    if kind == "sun":
        _sun(draw, canvas, canvas * 0.50, canvas * 0.50, canvas * 0.16)
    elif kind == "partly":
        _sun(draw, canvas, canvas * 0.36, canvas * 0.34, canvas * 0.11)
        _cloud(draw, canvas * 0.16, canvas * 0.40, canvas * 0.72)
    elif kind == "cloud":
        _cloud(draw, canvas * 0.12, canvas * 0.28, canvas * 0.76)
    elif kind == "fog":
        _fog(draw, canvas)
    elif kind == "drizzle":
        _cloud(draw, canvas * 0.14, canvas * 0.12, canvas * 0.72)
        _drops(draw, canvas * 0.30, canvas * 0.62, canvas, _RAIN, count=3, fat=0.035)
    elif kind == "rain":
        _cloud(draw, canvas * 0.14, canvas * 0.10, canvas * 0.72)
        _drops(draw, canvas * 0.28, canvas * 0.60, canvas, _RAIN, count=3, fat=0.045)
    elif kind == "heavy_rain":
        _cloud(draw, canvas * 0.12, canvas * 0.08, canvas * 0.76)
        _drops(draw, canvas * 0.22, canvas * 0.58, canvas, _RAIN, count=4, fat=0.048)
    elif kind == "snow":
        _cloud(draw, canvas * 0.14, canvas * 0.10, canvas * 0.72)
        _flakes(draw, canvas * 0.30, canvas * 0.62, canvas)
    elif kind == "sleet":
        _cloud(draw, canvas * 0.14, canvas * 0.08, canvas * 0.72)
        _drops(draw, canvas * 0.26, canvas * 0.58, canvas, _RAIN, count=2, fat=0.04)
        _flakes(draw, canvas * 0.52, canvas * 0.62, canvas, count=2)
    elif kind == "storm":
        _cloud(draw, canvas * 0.12, canvas * 0.06, canvas * 0.76)
        _bolt(draw, canvas * 0.46, canvas * 0.58, canvas)
        if code in (96, 99):
            _drops(draw, canvas * 0.62, canvas * 0.70, canvas, _SNOW, count=2, fat=0.03)
    else:
        _cloud(draw, canvas * 0.12, canvas * 0.28, canvas * 0.76)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def _kind(code: int | None) -> str:
    if code == 0:
        return "sun"
    if code in (1, 2):
        return "partly"
    if code == 3:
        return "cloud"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55):
        return "drizzle"
    if code in (61, 63, 80, 81):
        return "rain"
    if code in (65, 82):
        return "heavy_rain"
    if code in (56, 57, 66, 67):
        return "sleet"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    return "cloud"


def _sun(draw: ImageDraw.ImageDraw, _canvas: int, cx: float, cy: float, radius: float) -> None:
    width = max(4, int(radius * 0.28))
    for i in range(8):
        angle = math.radians(i * 45)
        inner = radius * 1.45
        outer = radius * 2.2
        draw.line(
            (
                cx + math.cos(angle) * inner,
                cy + math.sin(angle) * inner,
                cx + math.cos(angle) * outer,
                cy + math.sin(angle) * outer,
            ),
            fill=_SUN,
            width=width,
        )
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_SUN)


def _cloud(draw: ImageDraw.ImageDraw, x: float, y: float, width: float) -> None:
    height = width * 0.62
    draw.ellipse((x + width * 0.06, y + height * 0.36, x + width * 0.48, y + height * 1.02), fill=_CLOUD)
    draw.ellipse((x + width * 0.26, y + height * 0.02, x + width * 0.70, y + height * 0.78), fill=_CLOUD)
    draw.ellipse((x + width * 0.50, y + height * 0.30, x + width * 0.96, y + height * 0.98), fill=_CLOUD)
    draw.rectangle((x + width * 0.20, y + height * 0.55, x + width * 0.80, y + height * 0.96), fill=_CLOUD)


def _drops(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    canvas: int,
    color: tuple[int, int, int, int],
    *,
    count: int,
    fat: float,
) -> None:
    gap = canvas * 0.14
    for i in range(count):
        dx = x + i * gap
        dy = y + (i % 2) * canvas * 0.05
        draw.ellipse((dx, dy, dx + canvas * fat, dy + canvas * fat * 2.1), fill=color)


def _flakes(draw: ImageDraw.ImageDraw, x: float, y: float, canvas: int, count: int = 3) -> None:
    gap = canvas * 0.15
    arm = canvas * 0.035
    stroke = max(3, int(canvas * 0.012))
    for i in range(count):
        cx = x + i * gap
        cy = y + (i % 2) * canvas * 0.05
        draw.line((cx - arm, cy, cx + arm, cy), fill=_SNOW, width=stroke)
        draw.line((cx, cy - arm, cx, cy + arm), fill=_SNOW, width=stroke)


def _bolt(draw: ImageDraw.ImageDraw, cx: float, cy: float, canvas: int) -> None:
    w = canvas * 0.055
    h = canvas * 0.20
    draw.polygon(
        (
            (cx - w * 0.15, cy - h * 0.55),
            (cx + w * 1.05, cy - h * 0.55),
            (cx + w * 0.15, cy - h * 0.02),
            (cx + w * 0.85, cy - h * 0.02),
            (cx - w * 0.95, cy + h * 0.62),
            (cx - w * 0.05, cy + h * 0.08),
            (cx - w * 0.70, cy + h * 0.08),
        ),
        fill=_BOLT,
    )


def _fog(draw: ImageDraw.ImageDraw, canvas: int) -> None:
    spans = (0.70, 0.52, 0.70, 0.44)
    thickness = canvas * 0.055
    for i, span in enumerate(spans):
        y = canvas * (0.26 + i * 0.15)
        width = canvas * span
        x = (canvas - width) / 2
        draw.rounded_rectangle((x, y, x + width, y + thickness), radius=thickness / 2, fill=_FOG)
