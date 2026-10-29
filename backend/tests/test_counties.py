from app.render.counties import county_overlays
from app.render.ridge_geo import display_radar_bbox


def test_display_bbox_includes_collin_county():
    bbox = display_radar_bbox()
    overlays = county_overlays(bbox, 1024, 600)
    names = [label[0] for _rings, label in overlays if label]
    assert "Collin" in names
    assert "Dallas" in names
    assert len(overlays) >= 8
