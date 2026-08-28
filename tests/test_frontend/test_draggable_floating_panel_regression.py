"""Regression test for Draggable Floating Panel and Forecast Timeline Dock.

Validates:
1. useDraggableFloatingPanel hook supports baseTransform option and combines it with drag offsets without overwriting centered CSS transform.
2. handlePointerDown in useDraggableFloatingPanel refines no-drag checks so ancestor wrappers outside handle do not block dragging from title.
3. SuperMap DraggableTimelineDock passes baseTransform: "translateX(-50%)" to useDraggableFloatingPanel and does not wrap TimelineSlider in a no-drag container.
4. TimelineSlider preserves interactive range input and mark buttons while exposing titleProps for dragging.
5. Floating drawers (e.g. StationForecastDrawer) continue using useDraggableFloatingPanel safely without breaking.
"""

import re
from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
HOOK_FILE = FRONTEND_ROOT / "features" / "floating" / "useDraggableFloatingPanel.ts"
SUPER_MAP_FILE = FRONTEND_ROOT / "features" / "map" / "SuperMap.tsx"
TIMELINE_SLIDER_FILE = FRONTEND_ROOT / "features" / "stations" / "TimelineSlider.tsx"
FORECAST_DRAWER_FILE = FRONTEND_ROOT / "features" / "drawers" / "StationForecastDrawer.tsx"


class TestUseDraggableFloatingPanelHookContract:
    """Test suite for useDraggableFloatingPanel hook baseTransform and no-drag handling."""

    def setup_method(self):
        self.content = HOOK_FILE.read_text(encoding="utf-8")

    def test_options_interface_has_base_transform(self):
        """UseDraggableFloatingPanelOptions interface must include optional baseTransform property."""
        assert "baseTransform?: string;" in self.content

    def test_hook_destructures_base_transform(self):
        """Hook implementation must accept and destructure baseTransform."""
        assert "baseTransform," in self.content

    def test_panel_style_combines_base_transform_with_offset(self):
        """panelStyle must combine baseTransform with translate3d offset when offset is present."""
        assert "if (baseTransform) {" in self.content
        assert "${baseTransform} ${offsetStr}" in self.content

    def test_handle_pointer_down_checks_no_drag_inside_handle(self):
        """handlePointerDown must check if noDragEl is contained within handleEl."""
        assert "const noDragEl = target.closest('[data-no-drag=\"true\"], .no-drag');" in self.content
        assert "if (noDragEl && handleEl && handleEl.contains(noDragEl)) {" in self.content


class TestSuperMapTimelineDockContract:
    """Test suite for SuperMap timeline dock dragging configuration."""

    def setup_method(self):
        self.content = SUPER_MAP_FILE.read_text(encoding="utf-8")

    def test_timeline_dock_uses_base_transform_translate_x_50(self):
        """DraggableTimelineDock must pass baseTransform: 'translateX(-50%)' to useDraggableFloatingPanel."""
        assert 'panelId: "timeline",' in self.content
        assert 'baseTransform: "translateX(-50%)"' in self.content

    def test_timeline_slider_is_not_wrapped_in_no_drag_div(self):
        """SuperMap must not wrap TimelineSlider inside a data-no-drag='true' or no-drag container."""
        pattern = r'<div[^>]*className="[^"]*no-drag[^"]*"[^>]*>\s*<TimelineSlider'
        assert not re.search(pattern, self.content), "TimelineSlider must not be wrapped in no-drag container in SuperMap"
        assert 'data-no-drag="true"' not in self.content or '<TimelineSlider' not in self.content.split('data-no-drag="true"')[1].split('/>')[0]


class TestTimelineSliderComponentContract:
    """Test suite for TimelineSlider interactive elements and drag handle props."""

    def setup_method(self):
        self.content = TIMELINE_SLIDER_FILE.read_text(encoding="utf-8")

    def test_title_element_receives_title_props(self):
        """TimelineSlider header title must spread titleProps for dragging."""
        assert '<div className="timeline-slider-title" {...titleProps}>' in self.content

    def test_contains_range_input_and_mark_buttons(self):
        """TimelineSlider must render range input and mark buttons for step selection."""
        assert 'type="range"' in self.content
        assert 'className={`timeline-slider-mark' in self.content


class TestDrawerFloatingHookSafetyContract:
    """Test suite ensuring drawers continue to use useDraggableFloatingPanel safely."""

    def setup_method(self):
        self.content = FORECAST_DRAWER_FILE.read_text(encoding="utf-8")

    def test_forecast_drawer_uses_draggable_floating_panel(self):
        """StationForecastDrawer must use useDraggableFloatingPanel with panelId station-forecast."""
        assert 'useDraggableFloatingPanel({' in self.content
        assert 'panelId: "station-forecast"' in self.content


class TestMapIntelligencePanelsDragAndToggleContract:
    """Test suite ensuring MapIntelligencePanels (Air Quality Now) has drag and toggle visibility."""

    def setup_method(self):
        self.panels_file = FRONTEND_ROOT / "features" / "map" / "MapIntelligencePanels.tsx"
        self.app_file = FRONTEND_ROOT / "App.tsx"
        self.popover_file = FRONTEND_ROOT / "features" / "navigation" / "MapLayersPopover.tsx"
        self.panels_content = self.panels_file.read_text(encoding="utf-8")
        self.app_content = self.app_file.read_text(encoding="utf-8")
        self.popover_content = self.popover_file.read_text(encoding="utf-8")

    def test_map_intelligence_panels_uses_draggable_floating_panel(self):
        """MapIntelligencePanels must use useDraggableFloatingPanel with air-quality-now panelId."""
        assert 'useDraggableFloatingPanel({' in self.panels_content
        assert 'panelId: "air-quality-now"' in self.panels_content

    def test_map_intelligence_panels_binds_handle_props_to_header(self):
        """MapIntelligencePanels must bind handleProps to kicker header."""
        assert '{...containerProps}' in self.panels_content
        assert '{...handleProps}' in self.panels_content

    def test_app_conditionally_renders_air_quality_now(self):
        """App.tsx must conditionally render MapIntelligencePanels based on showAirQualityNow."""
        assert 'showAirQualityNow' in self.app_content
        assert '{(layerConfig.showAirQualityNow ?? true) && (' in self.app_content

    def test_popover_includes_toggle_for_air_quality_now(self):
        """MapLayersPopover must render checkbox toggle for showAirQualityNow."""
        assert 'toggle-air-quality-now' in self.popover_content
        assert 'showAirQualityNow' in self.popover_content


class TestMapLegendToggleContract:
    """Test suite ensuring Map Legend (AqiLegend) has toggle visibility and close button."""

    def setup_method(self):
        self.super_map_file = FRONTEND_ROOT / "features" / "map" / "SuperMap.tsx"
        self.aqi_legend_file = FRONTEND_ROOT / "features" / "map" / "AqiLegend.tsx"
        self.app_file = FRONTEND_ROOT / "App.tsx"
        self.popover_file = FRONTEND_ROOT / "features" / "navigation" / "MapLayersPopover.tsx"
        self.super_map_content = self.super_map_file.read_text(encoding="utf-8")
        self.aqi_legend_content = self.aqi_legend_file.read_text(encoding="utf-8")
        self.app_content = self.app_file.read_text(encoding="utf-8")
        self.popover_content = self.popover_file.read_text(encoding="utf-8")

    def test_super_map_conditionally_renders_draggable_legend_overlay(self):
        """SuperMap.tsx must conditionally render DraggableLegendOverlay based on showMapLegend."""
        assert '{(layerConfig.showMapLegend ?? true) && (' in self.super_map_content
        assert 'onCloseLegend={onToggleMapLegend}' in self.super_map_content

    def test_aqi_legend_supports_on_close(self):
        """AqiLegend.tsx must accept onClose prop and render legend close button."""
        assert 'onClose?: () => void;' in self.aqi_legend_content
        assert 'className="no-drag legend-close-btn"' in self.aqi_legend_content

    def test_app_initializes_show_map_legend(self):
        """App.tsx must initialize showMapLegend in layerConfig state."""
        assert 'showMapLegend: true' in self.app_content
        assert 'onToggleMapLegend={' in self.app_content

    def test_popover_includes_toggle_for_map_legend(self):
        """MapLayersPopover must render checkbox toggle for showMapLegend."""
        assert 'toggle-map-legend' in self.popover_content
        assert 'showMapLegend' in self.popover_content
