from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
LAYERS = (ROOT / "frontend" / "src" / "features" / "navigation" / "MapLayersPopover.tsx").read_text(encoding="utf-8")
MAP = (ROOT / "frontend" / "src" / "features" / "map" / "SuperMap.tsx").read_text(encoding="utf-8")
MARKERS = (ROOT / "frontend" / "src" / "features" / "map" / "VentilationDeviceMarkers.tsx").read_text(encoding="utf-8")
DRAWER = (ROOT / "frontend" / "src" / "features" / "drawers" / "DeviceDetailDrawer.tsx").read_text(encoding="utf-8")
STYLES = (ROOT / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")


def test_ventilation_layer_toggle_is_manager_only() -> None:
    assert "{isManager && (" in LAYERS
    assert "toggle-ventilation-devices" in LAYERS
    assert "isManager && layerConfig.showVentilationDevices" in MAP


def test_boost_marker_is_animated_but_respects_reduced_motion() -> None:
    assert 'return "boost"' in MARKERS
    assert "ventilation-marker--${modeClass" in MARKERS
    assert "ventilation-fan-spin" in STYLES
    assert "ventilation-pulse" in STYLES
    assert "prefers-reduced-motion" in STYLES


def test_device_drawer_shows_countdown_effectiveness_and_hitl_actions() -> None:
    assert "remainingSeconds" in DRAWER
    assert "pm25_reduction_percent" in DRAWER
    assert 'requestProposal("eco_mode")' in DRAWER
    assert 'requestProposal("standby")' in DRAWER
    assert "chỉ tạo proposal pending" in DRAWER
    assert "createVentilationDeviceProposal" in APP
    assert "refreshRevision={refreshRevision}" in APP
