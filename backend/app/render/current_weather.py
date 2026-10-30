from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.models.slideshow import WeatherSnapshot
from app.render.weather_icons import weather_icon

_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_CARD = (28, 28, 28)
_MUTED = (154, 160, 166)
_HINT = (197, 202, 208)
_WHITE = (255, 255, 255)


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    name = "Montserrat-SemiBold.ttf" if weight == "semibold" else "Montserrat-Regular.ttf"
    return ImageFont.truetype(_FONT_DIR / name, size)


def _uv_word(uv: float | None) -> str:
    if uv is None:
        return ""
    if uv < 3:
        return "Low"
    if uv < 6:
        return "Moderate"
    if uv < 8:
        return "High"
    if uv < 11:
        return "Very high"
    return "Extreme"


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


def render_current_weather_jpeg(
    weather: WeatherSnapshot | None,
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
    temp_font = _font("semibold", 72)
    cond_font = _font("regular", 32)
    feels_font = _font("regular", 22)
    cap_font = _font("regular", 20)
    value_font = _font("semibold", 30)
    hint_font = _font("regular", 18)

    draw.text((32, 26), "Current Weather", font=title_font, fill=_MUTED)

    if weather is None:
        draw.text((32, 100), "Weather unavailable", font=cond_font, fill=_WHITE)
    else:
        _draw_current(
            img,
            draw,
            weather,
            width,
            height,
            temp_font,
            cond_font,
            feels_font,
            cap_font,
            value_font,
            hint_font,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=90)
    return hashlib.sha256(out_path.read_bytes()).hexdigest()[:12]


def _temp(value: float | None) -> str:
    if value is None:
        return "--"
    return f"{value:.0f}°"


def _draw_current(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    weather: WeatherSnapshot,
    width: int,
    height: int,
    temp_font: ImageFont.FreeTypeFont,
    cond_font: ImageFont.FreeTypeFont,
    feels_font: ImageFont.FreeTypeFont,
    cap_font: ImageFont.FreeTypeFont,
    value_font: ImageFont.FreeTypeFont,
    hint_font: ImageFont.FreeTypeFont,
) -> None:
    icon_size = 200
    icon = weather_icon(weather.weather_code, icon_size)
    icon_x = 560 + (width - 36 - 560 - icon_size) / 2
    img.paste(icon, (int(round(icon_x)), 64), icon)

    draw.text((32, 86), _temp(weather.temperature_f), font=temp_font, fill=_WHITE)
    draw.text(
        (32, 178),
        weather.conditions or "Conditions unavailable",
        font=cond_font,
        fill=_WHITE,
    )
    draw.text((32, 226), f"Feels like {_temp(weather.feels_like_f)}", font=feels_font, fill=_MUTED)

    if weather.wind_direction:
        wind = f"{weather.wind_mph:.0f} mph  {weather.wind_direction}" if weather.wind_mph is not None else "--"
    elif weather.wind_mph is not None:
        wind = f"{weather.wind_mph:.0f} mph"
    else:
        wind = "--"
    humidity = "--" if weather.humidity_pct is None else f"{weather.humidity_pct:.0f}%"
    pressure = "--" if weather.pressure_inhg is None else f"{weather.pressure_inhg:.2f} in"
    uv_word = _uv_word(weather.uv_index)
    if weather.uv_index is None:
        uv = "--"
    elif uv_word:
        uv = f"{weather.uv_index:.0f}  {uv_word}"
    else:
        uv = f"{weather.uv_index:.0f}"

    cards = (
        ("Humidity", humidity, "Moisture in the air"),
        ("Wind", wind, "Sustained, with direction"),
        ("Pressure", pressure, "Rising often means fair"),
        ("UV", uv, "0 is low, 11 is extreme"),
    )
    margin = 28
    gap = 16
    top = 292
    card_h = 210
    card_w = (width - margin * 2 - gap * (len(cards) - 1)) / len(cards)
    for i, (caption, value, hint) in enumerate(cards):
        x = margin + i * (card_w + gap)
        _draw_card(draw, x, top, card_w, card_h, caption, value, hint, cap_font, value_font, hint_font)

    sunrise = weather.sunrise or "--"
    sunset = weather.sunset or "--"
    if weather.sunrise or weather.sunset:
        draw.text(
            (32, height - 48),
            f"Sunrise {sunrise}      Sunset {sunset}",
            font=feels_font,
            fill=_HINT,
        )


def _draw_card(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    w: float,
    h: float,
    caption: str,
    value: str,
    hint: str,
    cap_font: ImageFont.FreeTypeFont,
    value_font: ImageFont.FreeTypeFont,
    hint_font: ImageFont.FreeTypeFont,
) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=16, fill=_CARD)
    draw.text((x + 18, y + 18), caption, font=cap_font, fill=_MUTED)
    draw.text((x + 18, y + 52), value, font=value_font, fill=_WHITE)
    line_y = y + 108
    for line in _wrap(draw, hint, hint_font, int(w - 36)):
        draw.text((x + 18, line_y), line, font=hint_font, fill=_HINT)
        line_y += 24
