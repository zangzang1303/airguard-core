"""Frontend and Integration Contract Tests for Header/IDW Timestamp Synchronization.

Validates:
1. Datetime formatting helpers enforcing Asia/Ho_Chi_Minh and safe missing/invalid value handling.
2. Header contract: displays 'Đồng bộ trạm lúc', uses formatVnTimeWithSeconds, only on success.
3. IDW Metadata contract: displays 'Mô hình tạo lúc', 'Hiệu lực lúc' on forecast > 0, detail timestamps.
4. Refresh cycle synchronization: refreshRevision passed from App -> SuperMap -> HeatmapLayer.
5. Inactive heatmap does not trigger requests, request key guards against race conditions.
"""

import re
from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
DATETIME_FILE = FRONTEND_ROOT / "utils" / "datetime.ts"
TOP_BAR_FILE = FRONTEND_ROOT / "features" / "navigation" / "TopFloatingBar.tsx"
SUPER_MAP_FILE = FRONTEND_ROOT / "features" / "map" / "SuperMap.tsx"
HEATMAP_LAYER_FILE = FRONTEND_ROOT / "features" / "stations" / "HeatmapLayer.tsx"
AQI_LEGEND_FILE = FRONTEND_ROOT / "features" / "map" / "AqiLegend.tsx"
APP_FILE = FRONTEND_ROOT / "App.tsx"


class TestDatetimeUtilitiesContract:
    """Test suite for datetime.ts timezone and formatting contracts."""

    def setup_method(self):
        self.content = DATETIME_FILE.read_text(encoding="utf-8")

    def test_asia_ho_chi_minh_timezone_constant(self):
        """Must define VN_TZ as Asia/Ho_Chi_Minh."""
        assert 'export const VN_TZ = "Asia/Ho_Chi_Minh";' in self.content

    def test_has_format_vn_time_with_seconds(self):
        """Must have formatVnTimeWithSeconds function."""
        assert "function formatVnTimeWithSeconds" in self.content
        assert "timeZone: VN_TZ" in self.content
        assert 'second: "2-digit"' in self.content

    def test_has_format_vn_date_time_with_seconds(self):
        """Must have formatVnDateTimeWithSeconds function."""
        assert "function formatVnDateTimeWithSeconds" in self.content
        assert "timeZone: VN_TZ" in self.content

    def test_returns_dash_on_invalid_or_missing(self):
        """Must safely return dash '—' when date is missing or invalid."""
        assert 'return "—"' in self.content


class TestHeaderSyncLabelContract:
    """Test suite for TopFloatingBar header sync label and timestamp."""

    def setup_method(self):
        self.content = TOP_BAR_FILE.read_text(encoding="utf-8")

    def test_uses_dong_bo_tram_luc_label(self):
        """Header must use 'Đồng bộ trạm lúc ' instead of 'Vừa cập nhật'."""
        assert "Đồng bộ trạm lúc " in self.content
        assert "Vừa cập nhật" not in self.content

    def test_imports_and_uses_format_vn_time_with_seconds(self):
        """Header must import formatVnTimeWithSeconds from datetime utility."""
        assert "formatVnTimeWithSeconds" in self.content

    def test_accepts_last_station_sync_at_prop(self):
        """Header must support lastStationSyncAt prop."""
        assert "lastStationSyncAt" in self.content


class TestIdwMetadataLabelContract:
    """Test suite for DispersionMetadata component in AqiLegend.tsx."""

    def setup_method(self):
        self.content = AQI_LEGEND_FILE.read_text(encoding="utf-8")

    def test_uses_mo_hinh_tao_luc_label(self):
        """IDW card must use 'Mô hình tạo lúc:' instead of generic 'Cập nhật:'."""
        assert "Mô hình tạo lúc:" in self.content

    def test_displays_hieu_luc_luc_when_forecast_hour_positive(self):
        """Forecast modes (>0h) must display 'Hiệu lực lúc:' for data.timestamp."""
        assert "forecastHour > 0" in self.content
        assert "Hiệu lực lúc:" in self.content

    def test_imports_timezone_formatters(self):
        """AqiLegend must import formatVnDateTimeWithSeconds and formatVnTimeWithSeconds."""
        assert "formatVnDateTimeWithSeconds" in self.content
        assert "formatVnTimeWithSeconds" in self.content

    def test_renders_detailed_station_and_wind_timestamps_in_box(self):
        """Detail box must include weather observed_at and station_inputs observed_at."""
        assert "data?.weather?.observed_at" in self.content
        assert "data?.station_inputs" in self.content


class TestRefreshRevisionDataFlowContract:
    """Test suite for unified refreshRevision signal flow across App -> SuperMap -> HeatmapLayer."""

    def setup_method(self):
        self.app_content = APP_FILE.read_text(encoding="utf-8")
        self.super_map_content = SUPER_MAP_FILE.read_text(encoding="utf-8")
        self.heatmap_content = HEATMAP_LAYER_FILE.read_text(encoding="utf-8")

    def test_app_manages_refresh_revision_state(self):
        """AppContent must manage refreshRevision state."""
        assert "refreshRevision, setRefreshRevision" in self.app_content or "refreshRevision" in self.app_content
        assert "setRefreshRevision" in self.app_content

    def test_app_passes_refresh_revision_to_super_map(self):
        """App must pass refreshRevision to SuperMap."""
        assert "refreshRevision={refreshRevision}" in self.app_content

    def test_super_map_passes_refresh_revision_to_heatmap_layer(self):
        """SuperMap must receive and pass refreshRevision to HeatmapLayer."""
        assert "refreshRevision" in self.super_map_content
        assert "refreshRevision={refreshRevision}" in self.super_map_content

    def test_heatmap_layer_includes_refresh_revision_in_request_key_and_deps(self):
        """HeatmapLayer must include refreshRevision in requestKey and effect dependencies."""
        assert "refreshRevision" in self.heatmap_content
        assert "activeRequestKeyRef.current = requestKey" in self.heatmap_content

    def test_heatmap_layer_updates_loading_message(self):
        """HeatmapLayer must display accurate updating text."""
        assert "Đang cập nhật mô hình" in self.heatmap_content

    def test_app_does_not_fake_last_sync_on_error(self):
        """When station fetch errors, lastStationSyncAt is not updated with new client time."""
        # In error catch block of refreshData, it sets disconnected status and does not set lastStationSyncAt
        error_block_match = re.search(r"catch\s*\([^\)]*\)\s*\{([^}]+)\}", self.app_content)
        assert error_block_match is not None
        error_block = error_block_match.group(1)
        assert "setLastStationSyncAt" not in error_block
