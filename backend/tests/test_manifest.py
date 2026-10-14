from pathlib import Path

from app.manifest import build_slideshow_response
from app.state import DataStore


def test_slideshow_has_five_slides(tmp_path: Path):
    store = DataStore(tmp_path)
    store.set_revision("weather", "w1")
    store.set_revision("ham", "h1")
    store.set_revision("radar_reflectivity.jpg", "r1")
    store.set_revision("radar_velocity.jpg", "r2")
    store.set_revision("spc_day1_cat.jpg", "s1")

    resp = build_slideshow_response(store)
    assert len(resp.slides) == 5
    assert resp.slides[0].id == "current_weather"
    assert resp.slides[1].type == "image"
    assert "radar_reflectivity.jpg" in (resp.slides[1].url or "")
