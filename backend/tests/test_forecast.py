from pathlib import Path

from PIL import Image

from app.models.slideshow import ForecastDay
from app.render.forecast import render_forecast_jpeg


def test_forecast_jpeg_is_panel_sized(tmp_path: Path):
    days = [
        ForecastDay(
            day_label="Today" if i == 0 else "Sat",
            date_label=f"Oct {30 + i}",
            conditions="Partly cloudy" if i % 2 == 0 else "Thunderstorms",
            high_f=70 + i,
            low_f=48 + i,
            precip_pct=10 * i,
            weather_code=2 if i % 2 == 0 else 95,
        )
        for i in range(7)
    ]
    out = tmp_path / "forecast_7day.jpg"
    rev = render_forecast_jpeg(days, out, width=1024, height=600)
    assert len(rev) == 12
    with Image.open(out) as img:
        assert img.size == (1024, 600)


def test_weather_icons_are_visible():
    from app.render.weather_icons import weather_icon

    for code in (0, 2, 3, 45, 51, 63, 71, 95):
        icon = weather_icon(code, 68)
        assert icon.size == (68, 68)
        assert icon.getextrema()[-1][1] > 200
