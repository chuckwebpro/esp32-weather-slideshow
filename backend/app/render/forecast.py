from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.models.slideshow import ForecastDay

_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_CARD = (28, 28, 28)
_MUTED = (154, 160, 166)
_HINT = (197, 202, 208)
_WHITE = (255, 255, 255)
_RAIN = (138, 180, 248)


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    name = "Montserrat-SemiBold.ttf" if weight == "semibold" else "Montserrat-Regular.ttf"
    return ImageFont.truetype(_FONT_DIR / name, size)


def _accent(code: int | None) -> tuple[int, int, int]:
    if code in (0, 1):
        return (242, 184, 75)
    if code in (2, 3, 45, 48):
        return (148, 164, 184)
    if code in (71, 73, 75, 77, 85, 86):
        return (186, 214, 232)
    if code in (95, 96, 99):
        return (186, 140, 214)
    if code is None:
        return (90, 98, 110)
    return (110, 168, 214)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_w:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines[:3]


def render_forecast_jpeg(
    days: list[ForecastDay],
    out_path: Path,
    *,
    width: int | None = None,
    height: int | None = None,
) -> str:
    if width is None or height is None:
        from app.config import settings

        width = settings.image_width
        height = settings.image_height
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    title_font = _font("semibold", 28)
    day_font = _font("semibold", 26)
    date_font = _font("regular", 18)
    high_font = _font("semibold", 46)
    low_font = _font("regular", 22)
    body_font = _font("regular", 18)

    draw.text((24, 20), "7-Day Forecast", font=title_font, fill=_MUTED)

    if not days:
        draw.text((24, 80), "Forecast unavailable", font=day_font, fill=_WHITE)
    else:
        margin_x = 20
        gap = 12
        top = 78
        card_h = height - top - 20
        n = len(days)
        card_w = (width - margin_x * 2 - gap * (n - 1)) / n
        for i, day in enumerate(days):
            x = margin_x + i * (card_w + gap)
            _draw_day(draw, day, x, top, card_w, card_h, day_font, date_font, high_font, low_font, body_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=90)
    return hashlib.sha256(out_path.read_bytes()).hexdigest()[:12]


def _temp(value: float | None) -> str:
    if value is None:
        return "--"
    return f"{value:.0f}°"


def _draw_day(
    draw: ImageDraw.ImageDraw,
    day: ForecastDay,
    x: float,
    y: float,
    w: float,
    h: float,
    day_font: ImageFont.FreeTypeFont,
    date_font: ImageFont.FreeTypeFont,
    high_font: ImageFont.FreeTypeFont,
    low_font: ImageFont.FreeTypeFont,
    body_font: ImageFont.FreeTypeFont,
) -> None:
    right = x + w
    bottom = y + h
    draw.rounded_rectangle((x, y, right, bottom), radius=16, fill=_CARD)
    inset = 18
    draw.rectangle((x + inset, y, right - inset, y + 6), fill=_accent(day.weather_code))

    cx = x + w / 2
    text_w = int(w - 16)
    draw.text((cx, y + 28), day.day_label, font=day_font, fill=_WHITE, anchor="mt")
    draw.text((cx, y + 64), day.date_label, font=date_font, fill=_MUTED, anchor="mt")
    draw.text((cx, y + 128), _temp(day.high_f), font=high_font, fill=_WHITE, anchor="mt")
    low = _temp(day.low_f)
    draw.text((cx, y + 188), f"Low {low}", font=low_font, fill=_HINT, anchor="mt")

    lines = _wrap(draw, day.conditions, body_font, text_w)
    line_y = y + 250
    for line in lines:
        draw.text((cx, line_y), line, font=body_font, fill=_WHITE, anchor="mt")
        line_y += 26

    if day.precip_pct is None:
        rain = ""
    elif day.precip_pct <= 0:
        rain = "Dry"
    else:
        rain = f"{day.precip_pct}% rain"
    if rain:
        fill = _RAIN if day.precip_pct and day.precip_pct >= 30 else _HINT
        draw.text((cx, bottom - 48), rain, font=body_font, fill=fill, anchor="mt")
