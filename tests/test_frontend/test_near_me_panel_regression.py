"""Regression contracts for the Near Me panel and bottom navigation states."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
NEAR_ME_FILE = FRONTEND_SRC / "features" / "drawers" / "NearMePanel.tsx"
DOCK_FILE = FRONTEND_SRC / "features" / "navigation" / "BottomActionDock.tsx"
MAP_CONTROLS_FILE = FRONTEND_SRC / "features" / "map" / "MapLocationControls.tsx"
APP_FILE = FRONTEND_SRC / "App.tsx"
STYLES_FILE = FRONTEND_SRC / "styles.css"


class TestNearMePanelRegression:
    def setup_method(self):
        self.near_me = NEAR_ME_FILE.read_text(encoding="utf-8")
        self.dock = DOCK_FILE.read_text(encoding="utf-8")
        self.map_controls = MAP_CONTROLS_FILE.read_text(encoding="utf-8")
        self.app = APP_FILE.read_text(encoding="utf-8")
        self.styles = STYLES_FILE.read_text(encoding="utf-8")

    def test_near_me_controls_and_cards_have_scoped_styles(self):
        rendered_classes = (
            "near-me-location-switchers",
            "near-me-switch-btn",
            "near-me-current-loc-badge",
            "nearest-station-card",
            "nearest-secondary-metrics",
            "nearest-view-details-btn",
        )
        for class_name in rendered_classes:
            assert class_name in self.near_me
            assert f".{class_name}" in self.styles

    def test_map_pick_keeps_near_me_panel_open(self):
        assert "isPickingOnMap?: boolean" in self.near_me
        assert "onClick={onStartPickOnMap}" in self.near_me
        assert "onStartPickOnMap();\n                onClose();" not in self.near_me
        assert "Panel vẫn mở" in self.near_me
        assert "isPickingOnMap={isPickingOnMap}" in self.app

    def test_map_location_controls_do_not_fall_back_to_native_button_styles(self):
        for class_name in ("map-location-controls-floating", "map-fab-btn", "fab-tooltip"):
            assert class_name in self.map_controls
            assert f".{class_name}" in self.styles

    def test_layers_and_drawers_are_mutually_exclusive(self):
        assert "if (nextIsLayersOpen) setActiveDrawer(null);" in self.app
        assert "if (drawer !== null) setIsLayersOpen(false);" in self.app

    def test_dock_uses_pill_state_without_green_status_dots(self):
        assert "dock-active-dot" not in self.dock
        assert ".dock-active-dot" not in self.styles
        assert 'aria-pressed={isLayersOpen}' in self.dock
        assert 'aria-pressed={activeDrawer === "near-me"}' in self.dock

    def test_simulator_disclosure_is_explicit(self):
        assert "Dữ liệu từ trạm mô phỏng gần nhất" in self.near_me
        assert "không phải quan trắc chính thức" in self.near_me
