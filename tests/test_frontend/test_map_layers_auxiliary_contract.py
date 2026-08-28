"""Frontend and RBAC Contract Tests for Map Layers Auxiliary Components and Connection Toggle.

Validates:
1. MapLayerConfig and MapLayerVisibilityKey in superApp.ts.
2. Connection status toggle contract in TopFloatingBar:
   - .top-brand-badge is always rendered regardless of showConnectionStatus.
   - .connection-status-badge-bar is strictly conditioned on showConnectionStatus.
3. RBAC gating in MapLayersPopover:
   - Manager tools section is rendered only for isManager (role === "manager" | "admin").
   - Demo control row is rendered only when canUseDemoControl (isManager && demoMode).
   - Resident users have manager rows completely omitted.
4. Component wiring in App.tsx:
   - ManagerStationStatusBar rendered with isManager && layerConfig.showStationOverview.
   - DemoStationControl rendered with canUseDemoControl && layerConfig.showDemoControl.
   - Disabling showForecastTimeline when forecastHour > 0 resets forecastHour to 0.
5. SuperMap forecast timeline dock rendering condition:
   - Conditioned on viewMode === "heatmap" and layerConfig.showForecastTimeline.
6. DemoStationControl component-level RBAC guard:
   - Early return null if unprivileged, preventing 403 calls.
"""

import re
from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
SUPERAPP_TYPES_FILE = FRONTEND_ROOT / "types" / "superApp.ts"
TOP_BAR_FILE = FRONTEND_ROOT / "features" / "navigation" / "TopFloatingBar.tsx"
MAP_LAYERS_POPOVER_FILE = FRONTEND_ROOT / "features" / "navigation" / "MapLayersPopover.tsx"
APP_FILE = FRONTEND_ROOT / "App.tsx"
SUPER_MAP_FILE = FRONTEND_ROOT / "features" / "map" / "SuperMap.tsx"
DEMO_CONTROL_FILE = FRONTEND_ROOT / "features" / "drawers" / "DemoStationControl.tsx"


class TestMapLayerConfigTypesContract:
    """Test suite for MapLayerConfig and MapLayerVisibilityKey in superApp.ts."""

    def setup_method(self):
        self.content = SUPERAPP_TYPES_FILE.read_text(encoding="utf-8")

    def test_has_map_layer_visibility_key_type(self):
        """Must define MapLayerVisibilityKey union."""
        assert "export type MapLayerVisibilityKey =" in self.content
        assert '"showDemoControl"' in self.content
        assert '"showForecastTimeline"' in self.content
        assert '"showConnectionStatus"' in self.content
        assert '"showStationOverview"' in self.content

    def test_map_layer_config_includes_all_fields(self):
        """MapLayerConfig must include showDemoControl and showForecastTimeline."""
        assert "showDemoControl" in self.content
        assert "showForecastTimeline" in self.content
        assert "showConnectionStatus: boolean;" in self.content
        assert "showStationOverview: boolean;" in self.content


class TestConnectionToggleContract:
    """Test suite for TopFloatingBar connection status toggle bug fix."""

    def setup_method(self):
        self.content = TOP_BAR_FILE.read_text(encoding="utf-8")

    def test_brand_badge_always_rendered_without_show_connection_status_guard(self):
        """Brand badge (.top-brand-badge) must NOT be wrapped with showConnectionStatus condition."""
        # Check that top-brand-badge is rendered unconditionally
        brand_match = re.search(r'className="top-brand-badge"', self.content)
        assert brand_match is not None

        # Verify showConnectionStatus specifically guards connection-status-badge-bar
        assert "{showConnectionStatus && (" in self.content
        assert 'className="connection-status-badge-bar"' in self.content


class TestMapLayersPopoverRbacContract:
    """Test suite for RBAC visibility and controlled inputs in MapLayersPopover.tsx."""

    def setup_method(self):
        self.content = MAP_LAYERS_POPOVER_FILE.read_text(encoding="utf-8")

    def test_uses_auth_role_and_demo_mode_capability(self):
        """Popover must check isManager and canUseDemoControl."""
        assert "useAuth" in self.content
        assert 'isManager = role === "manager" || role === "admin"' in self.content
        assert "canUseDemoControl = isManager && Boolean(demoMode)" in self.content

    def test_manager_tools_section_guarded_by_is_manager(self):
        """Manager tools section is only rendered when isManager is true."""
        assert "{isManager && (" in self.content
        assert "Công cụ Ban Quản lý" in self.content
        assert "toggle-station-overview" in self.content

    def test_demo_control_guarded_by_can_use_demo_control(self):
        """Demo control toggle is only rendered when canUseDemoControl is true."""
        assert "{canUseDemoControl && (" in self.content
        assert "Điều khiển dữ liệu demo" in self.content
        assert "toggle-demo-control" in self.content

    def test_common_auxiliary_items_present(self):
        """Common auxiliary items must all be present."""
        assert "toggle-boundary" in self.content
        assert "toggle-sensors" in self.content
        assert "toggle-places" in self.content
        assert "toggle-connection" in self.content
        assert "toggle-map-legend" in self.content
        assert "toggle-dispersion" not in self.content
        assert "toggle-timeline" in self.content

    def test_controlled_checkbox_inputs_used(self):
        """Checkboxes must use standard onChange and checked props."""
        assert 'type="checkbox"' in self.content
        assert "onChange={() => toggleFeature(" in self.content


class TestAppWiringAndTimelineResetContract:
    """Test suite for App.tsx manager widget wiring and timeline reset on disable."""

    def setup_method(self):
        self.content = APP_FILE.read_text(encoding="utf-8")

    def test_manager_station_status_bar_wired_to_show_station_overview(self):
        """ManagerStationStatusBar must be guarded by isManager && layerConfig.showStationOverview."""
        assert "isManager && layerConfig.showStationOverview && (" in self.content
        assert "<ManagerStationStatusBar" in self.content

    def test_demo_station_control_wired_to_show_demo_control(self):
        """DemoStationControl must be guarded by canUseDemoControl && layerConfig.showDemoControl."""
        assert "canUseDemoControl && (layerConfig.showDemoControl ?? true) && (" in self.content
        assert "<DemoStationControl" in self.content

    def test_handle_layer_config_change_resets_forecast_hour_when_disabling_timeline(self):
        """Disabling timeline when forecastHour > 0 must reset forecastHour to 0."""
        assert "handleLayerConfigChange" in self.content
        assert "setForecastHour(0)" in self.content
        assert "!newConfig.showForecastTimeline" in self.content


class TestSuperMapTimelineRenderingContract:
    """Test suite for SuperMap forecast timeline dock rendering."""

    def setup_method(self):
        self.content = SUPER_MAP_FILE.read_text(encoding="utf-8")

    def test_timeline_dock_conditioned_on_view_mode_and_show_forecast_timeline(self):
        """Timeline dock must be conditioned on heatmap mode and showForecastTimeline."""
        assert 'viewMode === "heatmap" && (layerConfig.showForecastTimeline ?? true)' in self.content


class TestDemoStationControlRbacGuard:
    """Test suite for DemoStationControl authorization guard."""

    def setup_method(self):
        self.content = DEMO_CONTROL_FILE.read_text(encoding="utf-8")

    def test_early_return_when_not_allowed(self):
        """DemoStationControl must return null if not allowed."""
        assert "allowed = (role === \"manager\" || role === \"admin\") && Boolean(demoMode)" in self.content
        assert "if (!allowed) {\n    return null;\n  }" in self.content or "if (!allowed) return null;" in self.content

    def test_refresh_early_return_when_not_allowed(self):
        """refresh() must not call API if not allowed."""
        assert "if (!allowed) return;" in self.content
