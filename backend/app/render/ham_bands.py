from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.models.slideshow import HamSnapshot
from app.render.ham_icons import moon_icon, signal_level, signal_meter, sun_icon, wave_icon

_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_CARD = (28, 28, 28)
_MUTED = (154, 160, 166)
_HINT = (197, 202, 208)
_WHITE = (255, 255, 255)
_GOOD = (126, 204, 146)
_FAIR = (242, 196, 96)
_POOR = (224, 122, 122)

# N0NBH reports these ranges together. Together they cover 80 m through 10 m.
_BAND_ORDER = ("80m-40m", "30m-20m", "17m-15m", "12m-10m")
_BAND_LABELS = {
    "80m-40m": "80–40 m",
    "30m-20m": "30–20 m",
    "17m-15m": "17–15 m",
    "12m-10m": "12–10 m",
}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    name = "Montserrat-SemiBold.ttf" if weight == "semibold" else "Montserrat-Regular.ttf"
    return ImageFont.truetype(_FONT_DIR / name, size)


def _condition_color(value: str | None) -> tuple[int, int, int]:
    word = (value or "").strip().lower()
    if word == "good":
        return _GOOD
    if word == "fair":
        return _FAIR
    if word == "poor":
        return _POOR
    return _WHITE


def _rows(ham: HamSnapshot) -> list[tuple[str, str | None, str | None]]:
    by_name = {line.band: line for line in ham.bands}
    chosen = [by_name[name] for name in _BAND_ORDER if name in by_name]
    if not chosen:
        chosen = list(ham.bands)
    rows = []
    for line in chosen:
        rows.append((_BAND_LABELS.get(line.band, line.band), line.day, line.night))
    return rows


def _footer(ham: HamSnapshot) -> str:
    parts: list[str] = []
    if ham.sfi is not None:
        if ham.sfi >= 150:
            word = "excellent"
        elif ham.sfi >= 120:
            word = "good"
        elif ham.sfi >= 80:
            word = "fair"
        else:
            word = "low"
        parts.append(f"Solar flux {ham.sfi}, {word}")
    if ham.k_index is not None:
        if ham.k_index <= 1:
            word = "quiet"
        elif ham.k_index <= 3:
            word = "unsettled"
        elif ham.k_index <= 4:
            word = "active"
        else:
            word = "storm"
        parts.append(f"K {ham.k_index}, {word} right now")
    if ham.a_index is not None:
        if ham.a_index <= 7:
            word = "quiet"
        elif ham.a_index <= 15:
            word = "unsettled"
        elif ham.a_index <= 29:
            word = "active"
        else:
            word = "storm"
        parts.append(f"A {ham.a_index}, {word} today")
    return "   ·   ".join(parts)


def _paste_labeled(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    icon: Image.Image | None,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    gap: int = 10,
) -> None:
    text_width = draw.textlength(text, font=font)
    icon_w = icon.width if icon is not None else 0
    total = text_width + (icon_w + gap if icon is not None else 0)
    left = cx - total / 2
    if icon is not None:
        img.paste(icon, (int(round(left)), int(round(cy - icon.height / 2))), icon)
        left += icon_w + gap
    draw.text((left, cy), text, font=font, fill=fill, anchor="lm")


def render_ham_jpeg(
    ham: HamSnapshot | None,
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
    title_font = _font("regular", 22)
    header_font = _font("regular", 20)
    band_font = _font("semibold", 32)
    cond_font = _font("semibold", 28)
    foot_font = _font("regular", 18)

    mark = wave_icon(30)
    img.paste(mark, (28, 16), mark)
    draw.text((68, 22), "HF Band Conditions", font=title_font, fill=_MUTED)

    rows = _rows(ham) if ham is not None else []
    if not rows:
        draw.text((32, 90), "Band report unavailable", font=band_font, fill=_WHITE)
    else:
        margin = 28
        card_w = width - margin * 2
        day_x = margin + card_w * 0.62
        night_x = margin + card_w * 0.86
        header_y = 88
        _paste_labeled(img, draw, day_x, header_y, sun_icon(26), "Day", header_font, _MUTED)
        _paste_labeled(img, draw, night_x, header_y, moon_icon(26), "Night", header_font, _MUTED)

        top = 118
        gap = 12
        card_h = 94
        for i, (label, day, night) in enumerate(rows):
            y = top + i * (card_h + gap)
            cy = y + card_h / 2
            draw.rounded_rectangle((margin, y, margin + card_w, y + card_h), radius=16, fill=_CARD)
            draw.text((margin + 28, cy), label, font=band_font, fill=_WHITE, anchor="lm")
            _paste_condition(img, draw, day_x, cy, day, cond_font)
            _paste_condition(img, draw, night_x, cy, night, cond_font)

    if ham is not None:
        footer = _footer(ham)
        if footer:
            foot_y = height - 28
            sun = sun_icon(22)
            img.paste(sun, (32, int(foot_y - sun.height / 2)), sun)
            draw.text((62, foot_y), footer, font=foot_font, fill=_HINT, anchor="lm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=90)
    return hashlib.sha256(out_path.read_bytes()).hexdigest()[:12]


def _paste_condition(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    value: str | None,
    font: ImageFont.FreeTypeFont,
) -> None:
    text = value or "—"
    color = _condition_color(value)
    level = signal_level(value)
    meter = signal_meter(level, color, 34) if level else None
    _paste_labeled(img, draw, cx, cy, meter, text, font, color, gap=8)
