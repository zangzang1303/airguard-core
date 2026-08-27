from __future__ import annotations

from pathlib import Path

CONTROLLER = Path("frontend/src/features/map/MapActionController.ts")


def test_route_overlay_renders_backend_environment_segments():
    content = CONTROLLER.read_text(encoding="utf-8")

    assert "action.segments" in content
    assert "spatial_idw_route_segment" not in content
    assert "segmentColorMap" in content
    assert "unhealthy_sensitive" in content
    assert "segmentPolyline.bindTooltip" in content
    assert "PM2.5" in content


def test_route_overlay_keeps_unsegmented_contract_compatible():
    content = CONTROLLER.read_text(encoding="utf-8")

    assert "segments.length === 0" in content
    assert "corePolyline" in content
