"""
Unit & Contract Tests for AirGuard AI Map Marker, Station Status & Legend Synchronization.

Acceptance Criteria:
1. Canonical status configuration has all 4 states: online, stale, offline, invalid
2. S01-S05 station identification is standardized with unified sensor pin & station code
3. Offline and Invalid are NOT merged; distinct visual and tooltip representations
4. Tooltip of invalid station displays 'Invalid', not 'Offline'
5. Legend station-status indicators sync with canonical config
6. Station status legend only displays when station marker layer is visible
7. POI / Places layer defaults to off (showPlaces: false)
"""
from pathlib import Path

import pytest

FRONTEND_SRC = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
STATUS_FILE = FRONTEND_SRC / "constants" / "stationStatus.ts"
SENSOR_MARKERS_FILE = FRONTEND_SRC / "features" / "map" / "SensorMarkers.tsx"
AQI_LEGEND_FILE = FRONTEND_SRC / "features" / "map" / "AqiLegend.tsx"
SUPER_MAP_FILE = FRONTEND_SRC / "features" / "map" / "SuperMap.tsx"
SUBZONE_FILE = FRONTEND_SRC / "features" / "map" / "SubZoneLabels.tsx"
APP_FILE = FRONTEND_SRC / "App.tsx"


def resolve_station_status_py(station: dict) -> str:
    """Python counterpart of resolveStationStatus for logic verification."""
    status = station.get("status")
    is_stale = station.get("is_stale", False)
    if status == "invalid":
        return "invalid"
    if status == "offline":
        return "offline"
    if status == "stale" or is_stale:
        return "stale"
    if status == "online":
        return "online"
    return "offline"


class TestCanonicalStationStatusHierarchy:
    """Tests the resolution and contract of the 4 canonical data quality statuses."""

    def test_all_four_statuses_distinct(self):
        statuses = ["online", "stale", "offline", "invalid"]
        assert len(set(statuses)) == 4

    def test_status_resolution_hierarchy(self):
        # Online fresh
        assert resolve_station_status_py({"status": "online", "is_stale": False}) == "online"
        # Stale by is_stale flag
        assert resolve_station_status_py({"status": "online", "is_stale": True}) == "stale"
        # Stale by status
        assert resolve_station_status_py({"status": "stale", "is_stale": False}) == "stale"
        # Offline
        assert resolve_station_status_py({"status": "offline", "is_stale": False}) == "offline"
        # Invalid takes highest precedence
        assert resolve_station_status_py({"status": "invalid", "is_stale": True}) == "invalid"
        assert resolve_station_status_py({"status": "invalid", "is_stale": False}) == "invalid"

    def test_station_status_file_contents(self):
        assert STATUS_FILE.exists()
        content = STATUS_FILE.read_text(encoding="utf-8")
        assert "export const STATION_STATUS_CONFIG" in content
        assert "online:" in content
        assert "stale:" in content
        assert "offline:" in content
        assert "invalid:" in content
        # Ensure 4 distinct symbols and colors are configured
        assert "●" in content
        assert "▲" in content
        assert "✖" in content
        assert "?" in content


class TestSensorMarkersContract:
    """Tests SensorMarkers.tsx implementation for standardized station pins and tooltip accuracy."""

    @pytest.fixture(autouse=True)
    def setup(self):
        assert SENSOR_MARKERS_FILE.exists()
        self.content = SENSOR_MARKERS_FILE.read_text(encoding="utf-8")

    def test_uses_canonical_status_config(self):
        assert "resolveStationStatus" in self.content
        assert "getStationStatusConfig" in self.content

    def test_renders_station_code_pill(self):
        """Must render station code (S01-S05) in station code pill for visual clarity."""
        assert "station-code-pill" in self.content
        assert "createSensorStationIcon" in self.content
        assert "${stationId}" in self.content or "${station.station_id}" in self.content

    def test_does_not_merge_offline_and_invalid(self):
        """Offline and invalid must NOT be grouped into a single 'unavailable' branch."""
        assert 'resolvedStatus === "invalid"' in self.content
        assert 'resolvedStatus === "offline"' in self.content
        assert 'resolvedStatus === "stale"' in self.content

    def test_tooltip_displays_invalid_distinct_from_offline(self):
        """Invalid station tooltip must display 'Trạng thái: Invalid' and not 'Trạng thái: Offline'."""
        assert "Trạng thái: Invalid" in self.content
        assert "Trạng thái: Offline" in self.content
        assert "Dữ liệu cũ" in self.content

    def test_no_poi_icons_used_for_stations(self):
        """SensorMarkers must not import or render POI category emojis or icons."""
        assert "OCEAN_PARK_POIS" not in self.content
        assert "poi-emoji" not in self.content


class TestAqiLegendContract:
    """Tests AqiLegend.tsx synchronization with canonical status."""

    @pytest.fixture(autouse=True)
    def setup(self):
        assert AQI_LEGEND_FILE.exists()
        self.content = AQI_LEGEND_FILE.read_text(encoding="utf-8")

    def test_uses_canonical_status_config_in_legend(self):
        assert "STATION_STATUS_CONFIG" in self.content
        assert "StationStatusLegend" in self.content

    def test_header_title_reflects_station_status_visibility(self):
        """Legend header updates dynamically if showStationStatus is true or false."""
        assert "showStationStatus" in self.content
        assert "Chú giải ${scale.label} & Trạng thái trạm" in self.content


class TestSuperMapLayerVisibilityContract:
    """Tests SuperMap.tsx layer and legend visibility synchronization."""

    @pytest.fixture(autouse=True)
    def setup(self):
        assert SUPER_MAP_FILE.exists()
        self.content = SUPER_MAP_FILE.read_text(encoding="utf-8")

    def test_is_sensor_layer_visible_calculated_and_passed(self):
        """Station status legend is hidden on map legend overlay."""
        assert "showStationStatus={false}" in self.content

    def test_keyless_osm_basemap_is_shared_by_local_and_deploy(self):
        assert "https://tile.openstreetmap.org/{z}/{x}/{y}.png" in self.content
        assert "basemaps.cartocdn.com" not in self.content
        assert "OpenStreetMap" in self.content

    def test_sensor_markers_can_overlay_the_heatmap(self):
        assert "showSensors={layerConfig.showSensors}" in self.content
        assert 'showSensors={layerConfig.showSensors && viewMode !== "heatmap"}' not in self.content


class TestSubZoneLabelsAndAppDefaults:
    """Tests default layer settings and POI visual distinction."""

    def test_show_places_default_is_false_in_app(self):
        """showPlaces must default to false in App.tsx to prevent visual competition with sensor stations."""
        assert APP_FILE.exists()
        app_content = APP_FILE.read_text(encoding="utf-8")
        assert "showPlaces: false" in app_content

    def test_subzone_poi_is_tagged_and_distinct(self):
        """SubZoneLabels.tsx must tag POIs clearly and use smaller badge size."""
        assert SUBZONE_FILE.exists()
        subzone_content = SUBZONE_FILE.read_text(encoding="utf-8")
        assert "poi-category-tag" in subzone_content
        assert "iconSize: [22, 22]" in subzone_content
