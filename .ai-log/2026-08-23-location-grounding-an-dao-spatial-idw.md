# AI Work Log: Fix Location Grounding & Geospatial Context Resolution (An Đào vs San Hô)

**Date**: 2026-08-23
**Focus**: Root-cause fix for entity parsing, location precedence, IDW spatial interpolation for subdivisions without physical sensors, and map action synchronization.

---

## 1. Problem Description

- **Symptom**: When user asked `chất lượng không khí tại an đào`, the agent answered with data from `Công viên San Hô` (or whichever sensor/POI was currently selected in map context).
- **Root Causes Identified**:
  1. `SpatialRegistry` only contained 5 POIs with direct 1-to-1 sensor mapping. Real estate / residential subdivisions without dedicated physical sensors (such as *Biệt thự An Đào*, *Sao Biển*, *Đảo Ngọc Trai*, *Zenpark*, etc.) were missing from canonical POI definitions.
  2. `extract_location_in_query` did not properly isolate explicit entity names from prepositional context vs interrogative phrases.
  3. Precedence rule was inverted in `geospatial_agent_service.py` (`selected_location` was overriding explicit user queries).
  4. Non-sensor subdivisions lacked dynamic IDW (Inverse Distance Weighting) spatial interpolation integration with the agent runtime.
  5. Fallback mechanism for unknown locations outside Ocean Park 1 silently fell back to active map selection rather than failing closed with informative explanation.

---

## 2. Changes Made

1. **Spatial Registry Database Overhaul (`backend/app/services/spatial_registry.py`)**:
   - Registered `poi_an_dao` (Phân khu Biệt thự An Đào, `lat: 20.9995, lng: 105.9415`, `is_interpolated=True`, `source_sensors: ["S01", "S02"]`).
   - Registered remaining Ocean Park 1 subdivisions: `poi_sao_bien`, `poi_dao_ngoc_trai`, `poi_zenpark_ruby`, `poi_pavilion_zurich`, `poi_vinschool`, `poi_vinmec`, `poi_da_ton`.
   - Added `SpatialRegistry.interpolate_environment_at_point(lat, lon, station_data_map)`: Reuses shared standard Inverse Distance Weighting ($p=2.0$) over active physical sensors.
   - Refined `extract_location_in_query` with unaccented tokenization, alias length ordering, and robust stopword filtering to distinguish explicit places from general queries (e.g. `khu vực nào đang ô nhiễm nhất`).

2. **Geospatial Agent Pipeline (`backend/app/services/geospatial_agent_service.py`)**:
   - Dynamically populates `candidate_pois` with IDW environmental data for interpolated POIs alongside physical sensor POIs.
   - Enforced strict 5-tier location precedence:
     `Explicit query location > Conversation follow-up > Map selected location / sensor > User location > Default ranked POI`.
   - Updated `_handle_single_location_intent`:
     - Explains IDW estimation transparently: *"Chất lượng không khí ước tính tại An Đào hiện ở mức AQI... dựa trên dữ liệu quan trắc từ các trạm lân cận (Trạm S01, Trạm S02)"*.
     - Returns grounded evidence: `{"method": "idw_spatial_interpolation", "is_interpolated": True, "source_sensors": ["S01", "S02"], ...}`.
     - Emits synchronized map actions (`fly_to`, `highlight_area`, `add_annotation` targeting `poi_an_dao` at `20.9995, 105.9415`).
   - Added `_handle_unknown_location_intent`: Handles unknown locations (e.g. `chất lượng không khí tại ABCXYZ`) cleanly without leaking state.
   - Enhanced `_handle_comparison_intent` to support dynamic POI pairs (e.g. comparing An Đào with Hồ Ngọc Trai).

3. **Conversational Agent Gate (`backend/app/services/conversational_agent_service.py`)**:
   - Added Ocean Park 1 POI alias signals (`an dao`, `zenpark`, `ruby`, `zurich`, `pavilion`, `vincom`, `vinschool`, `vinmec`, `da ton`, `bien ho`) to ensure domain queries are correctly routed to the geospatial engine.

4. **Automated Regression Test Suite (`tests/test_backend/test_geospatial_agent.py`)**:
   - `test_an_dao_location_grounding_overrides_active_map_selection`
   - `test_deictic_query_without_explicit_name_uses_map_selection`
   - `test_unknown_location_outside_ocean_park_fails_closed`
   - `test_comparison_between_interpolated_and_physical_poi`

---

## 3. Verification & Test Results

- All **374/374 pytest tests passed 100% in 7.24s**.
- Zero regressions across grounding, evaluation, proposals, and IoT simulator test suites.
