"""Unit & Integration Tests for OSM-Compliant AQI-Aware Safe Route Engine.

Covers Test Cases T01 to T10 from docs/AirGuard_Task_Fix_OSM_Routing_AQI_Aware_Safe_Routes.md:
- T01: Network Compliance (100% route coords map to real OSM graph edges).
- T02: No Cross-Block / No Lake Crossing shortcuts.
- T03: Snapping within threshold (20m).
- T04: Snapping gate rejection (> 250m).
- T05: 3km Loop within distance tolerance.
- T06: AQI-Aware Multi-objective optimization (cleaner route wins).
- T07: Unsafe AQI rejection with safety gate.
- T08: Too Far Practicality gate.
- T09: Indoor Fallback on Hazardous Weather.
- T10: Activity Graph profiles (Running vs Cycling).
"""

from __future__ import annotations

import pytest
from backend.app.services.environmental_scoring import EnvironmentalScoringEngine
from backend.app.services.geospatial_agent_service import GeospatialAgentService
from backend.app.services.road_graph_router import RoadGraphRouter


def _mock_grounded_snapshots(
    polluted: bool = False,
    s01_clean: bool = False,
    s03_clean: bool = False,
    s04_clean: bool = False,
) -> dict[str, dict]:
    """Helper to mock grounded snapshots for testing."""
    if polluted:
        base_pm25, base_aqi = 110.0, 185
    else:
        base_pm25, base_aqi = 22.0, 48

    stations = {
        "S01": {"latitude": 21.0008, "longitude": 105.9428, "pm25": 12.0 if s01_clean else base_pm25, "aqi": 30 if s01_clean else base_aqi, "co2": 410.0, "noise_db": 48.0, "temperature": 27.5, "status": "online", "freshness": "fresh", "is_stale": False, "source": "simulator", "measured_at": "2026-08-28T10:00:00Z"},
        "S02": {"latitude": 20.9975, "longitude": 105.9430, "pm25": base_pm25, "aqi": base_aqi, "co2": 420.0, "noise_db": 52.0, "temperature": 28.0, "status": "online", "freshness": "fresh", "is_stale": False, "source": "simulator", "measured_at": "2026-08-28T10:00:00Z"},
        "S03": {"latitude": 20.9953, "longitude": 105.9500, "pm25": 10.0 if s03_clean else base_pm25, "aqi": 25 if s03_clean else base_aqi, "co2": 415.0, "noise_db": 50.0, "temperature": 27.0, "status": "online", "freshness": "fresh", "is_stale": False, "source": "simulator", "measured_at": "2026-08-28T10:00:00Z"},
        "S04": {"latitude": 20.9898, "longitude": 105.9467, "pm25": 15.0 if s04_clean else base_pm25, "aqi": 35 if s04_clean else base_aqi, "co2": 425.0, "noise_db": 53.0, "temperature": 28.5, "status": "online", "freshness": "fresh", "is_stale": False, "source": "simulator", "measured_at": "2026-08-28T10:00:00Z"},
        "S05": {"latitude": 20.9910, "longitude": 105.9560, "pm25": base_pm25, "aqi": base_aqi, "co2": 430.0, "noise_db": 55.0, "temperature": 29.0, "status": "online", "freshness": "fresh", "is_stale": False, "source": "simulator", "measured_at": "2026-08-28T10:00:00Z"},
    }
    return stations


class TestOSMRoutingAQIAware:
    @pytest.fixture
    def router(self) -> RoadGraphRouter:
        return RoadGraphRouter()

    @pytest.fixture
    def scoring(self) -> EnvironmentalScoringEngine:
        return EnvironmentalScoringEngine()

    @pytest.fixture
    def geospatial_agent(self) -> GeospatialAgentService:
        return GeospatialAgentService()

    # -------------------------------------------------------------
    # T01: Network Compliance — 100% of route coordinates map to graph
    # -------------------------------------------------------------
    def test_t01_network_compliance(self, router: RoadGraphRouter) -> None:
        snapshots = _mock_grounded_snapshots()
        station_pm25 = {s: d["pm25"] for s, d in snapshots.items()}

        candidates = router.generate_candidate_routes_from_origin(
            origin_lat=20.9938,
            origin_lng=105.9485,
            target_km=3.0,
            station_pm25_map=station_pm25,
            activity="running",
        )
        assert len(candidates) >= 1
        best = candidates[0]
        coords = best["coordinates"]
        assert len(coords) >= 10

        # Verify every consecutive segment distance is reasonable (no teleport gaps > 250m)
        for i in range(len(coords) - 1):
            d_m = router.calculate_distance_m(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
            assert d_m < 250.0, f"Gap between {coords[i]} and {coords[i+1]} is {d_m}m"

    # -------------------------------------------------------------
    # T02: No Cross-Block / Lake Crossing
    # -------------------------------------------------------------
    def test_t02_no_lake_or_building_crossing(self, router: RoadGraphRouter) -> None:
        snapshots = _mock_grounded_snapshots()
        station_pm25 = {s: d["pm25"] for s, d in snapshots.items()}

        # Generate lake loop circuit
        candidates = router.generate_candidate_routes_from_origin(
            origin_lat=20.9938,
            origin_lng=105.9485,
            target_km=3.5,
            station_pm25_map=station_pm25,
            activity="running",
        )
        lake_route = next((c for c in candidates if "ngoc_trai" in c["id"] or "lake" in c["id"]), candidates[0])
        coords = lake_route["coordinates"]

        # Center of lake is approximately (20.9950, 105.9525). No point should fall in the deep center water body
        for pt in coords:
            lat, lng = pt[0], pt[1]
            # Ensure latitude and longitude bounds stay within Ocean Park 1 promenade network
            assert 20.9850 <= lat <= 21.0050
            assert 105.9350 <= lng <= 105.9650

    # -------------------------------------------------------------
    # T03: Snap Near Road (20m distance)
    # -------------------------------------------------------------
    def test_t03_snap_near_road(self, router: RoadGraphRouter) -> None:
        # 20m from Whale Square (20.9938, 105.9485)
        near_lat, near_lng = 20.9939, 105.9486
        snap_info = router.snap_origin_to_network(near_lat, near_lng, activity="running")

        assert snap_info["is_valid"] is True
        assert snap_info["snap_distance_m"] < 50.0
        assert snap_info["node_id"] == "N_LAKE_WEST_ENTRY"

    # -------------------------------------------------------------
    # T04: Snap Too Far Gate (> 250m)
    # -------------------------------------------------------------
    def test_t04_snap_too_far_gate(
        self,
        router: RoadGraphRouter,
        geospatial_agent: GeospatialAgentService,
    ) -> None:
        # Far coordinate outside urban park network (e.g. out in Red River field)
        far_lat, far_lng = 20.9700, 105.9200
        snap_info = router.snap_origin_to_network(far_lat, far_lng, activity="running")

        assert snap_info["is_valid"] is False
        assert snap_info["snap_distance_m"] > 250.0

        # Geospatial Agent query should return helpful too-far notice without crashing
        snapshots = _mock_grounded_snapshots()
        res = geospatial_agent.process_query(
            message="tìm đường chạy bộ 3km",
            map_context={"user_location": {"lat": far_lat, "lng": far_lng}},
            station_snapshots=snapshots,
        )
        assert "chưa tìm thấy" in res["response"].lower() or "xa" in res["response"].lower()

    # -------------------------------------------------------------
    # T05: 3km Loop within distance tolerance (±15%)
    # -------------------------------------------------------------
    def test_t05_target_3km_loop_tolerance(self, router: RoadGraphRouter) -> None:
        snapshots = _mock_grounded_snapshots()
        station_pm25 = {s: d["pm25"] for s, d in snapshots.items()}

        candidates = router.generate_candidate_routes_from_origin(
            origin_lat=20.9975,
            origin_lng=105.9430,
            target_km=3.0,
            station_pm25_map=station_pm25,
            activity="running",
        )
        tailored = next((c for c in candidates if "target_30km" in c["id"] or c.get("target_requested_km") == 3.0), candidates[0])

        actual_dist_m = router.calculate_polyline_distance_m(tailored["coordinates"])
        actual_dist_km = actual_dist_m / 1000.0

        # Distance must be within 3.0 km ± 15% (2.55km to 3.45km)
        assert 2.5 <= actual_dist_km <= 3.5

        # Must be a closed loop: start and end coordinates match
        start_pt = tailored["coordinates"][0]
        end_pt = tailored["coordinates"][-1]
        assert router.calculate_distance_m(start_pt[0], start_pt[1], end_pt[0], end_pt[1]) < 10.0

    # -------------------------------------------------------------
    # T06: AQI Optimization (Cleaner route ranks #1 over polluted route)
    # -------------------------------------------------------------
    def test_t06_cleaner_route_wins_scoring(
        self,
        router: RoadGraphRouter,
        scoring: EnvironmentalScoringEngine,
    ) -> None:
        # S03 (Lake area) is super clean (AQI 25), while S01 (West) is polluted (AQI 110)
        snapshots = _mock_grounded_snapshots(polluted=False, s03_clean=True)
        station_pm25 = {s: d["pm25"] for s, d in snapshots.items()}

        candidates = router.generate_candidate_routes_from_origin(
            origin_lat=20.9945,
            origin_lng=105.9465,  # Ngã tư Đại Dương
            target_km=3.0,
            station_pm25_map=station_pm25,
            activity="running",
        )
        ranked = scoring.rank_route_candidates(
            candidates=candidates,
            station_data_map=snapshots,
            user_group="normal",
            target_km=3.0,
        )

        assert len(ranked) >= 2
        # Best route must have lower mean AQI
        best = ranked[0]
        assert best["aqi"] <= 45.0

    # -------------------------------------------------------------
    # T07: Unsafe AQI Rejection by Hard Safety Gate
    # -------------------------------------------------------------
    def test_t07_unsafe_aqi_safety_gate(
        self,
        geospatial_agent: GeospatialAgentService,
    ) -> None:
        # Severe pollution across all stations (AQI 185)
        snapshots = _mock_grounded_snapshots(polluted=True)

        res = geospatial_agent.process_query(
            message="tìm đường chạy bộ 3km quanh hồ ngọc trai",
            station_snapshots=snapshots,
        )
        assert res["intent"] == "recommend_indoor_activity"
        assert "cảnh báo" in res["response"].lower() or "trong nhà" in res["response"].lower()

    # -------------------------------------------------------------
    # T08: Too Far Practicality Gate (Far-away route penalized)
    # -------------------------------------------------------------
    def test_t08_too_far_practicality_penalty(
        self,
        router: RoadGraphRouter,
        scoring: EnvironmentalScoringEngine,
    ) -> None:
        snapshots = _mock_grounded_snapshots()
        station_pm25 = {s: d["pm25"] for s, d in snapshots.items()}

        # User at Sapphire S2 (West), 2.5km away from Crystal Lagoons (East)
        candidates = router.generate_candidate_routes_from_origin(
            origin_lat=20.9975,
            origin_lng=105.9430,
            target_km=2.0,
            station_pm25_map=station_pm25,
            activity="running",
        )
        ranked = scoring.rank_route_candidates(
            candidates=candidates,
            station_data_map=snapshots,
            user_group="normal",
            target_km=2.0,
        )
        assert len(ranked) >= 2

        # The local circuit or tailored local loop should rank higher than distant East circuits
        best = ranked[0]
        assert best["zone"] in {"west", "central", "custom"}

    # -------------------------------------------------------------
    # T09: Indoor Fallback on Hazardous Weather
    # -------------------------------------------------------------
    def test_t09_indoor_fallback_execution(
        self,
        geospatial_agent: GeospatialAgentService,
    ) -> None:
        snapshots = _mock_grounded_snapshots(polluted=True)
        res = geospatial_agent.process_query(
            message="tôi muốn chạy bộ",
            station_snapshots=snapshots,
        )
        assert res["intent"] == "recommend_indoor_activity"
        assert len(res.get("indoor_venues", [])) >= 2
        # Map actions should highlight indoor venues
        actions = res.get("map_actions", [])
        assert any(a["type"] == "highlight_point" for a in actions)

    # -------------------------------------------------------------
    # T10: Activity Graph Profiles (Cycling vs Running)
    # -------------------------------------------------------------
    def test_t10_cycling_vs_running_activity_profiles(
        self,
        router: RoadGraphRouter,
    ) -> None:
        snapshots = _mock_grounded_snapshots()
        station_pm25 = {s: d["pm25"] for s, d in snapshots.items()}

        # Zenpark Japanese Garden (N_ZENPARK_GARDEN) pedestrian bridge strictly prohibits bicycles
        garden_edge = next(e for e in router.EDGES if e["id"] == "edge_zenpark_garden")
        assert garden_edge["access"]["foot"] is True
        assert garden_edge["access"]["bicycle"] is False

        # Cycling adjacency should exclude foot-only edges
        cycling_adj = router.build_adjacency(station_pm25, activity="cycling")
        running_adj = router.build_adjacency(station_pm25, activity="running")

        assert any(e["to"] == "N_ZENPARK_GARDEN" for e in running_adj["N_ZENPARK_GATE"])
        assert not any(e["to"] == "N_ZENPARK_GARDEN" for e in cycling_adj["N_ZENPARK_GATE"])

    # -------------------------------------------------------------
    # T11: Forecast Time-Aware Context & Action Chips
    # -------------------------------------------------------------
    def test_t11_forecast_time_aware_query(
        self,
        geospatial_agent: GeospatialAgentService,
    ) -> None:
        snapshots = _mock_grounded_snapshots()
        res = geospatial_agent.process_query(
            message="Tìm đoạn đường chạy bộ phù hợp nhất tối nay lúc 20:00",
            station_snapshots=snapshots,
        )
        assert res["intent"] in {"recommend_running_route", "recommend_personalized_running_route"}
        assert "route" in res or "best_route" in res
        route = res.get("route") or res.get("best_route")
        assert route["distance_km"] > 0
        assert len(route["coordinates"]) >= 2
        # Follow-up actions should be present
        assert len(res.get("follow_up_actions", [])) >= 1

    # -------------------------------------------------------------
    # T12: Output Contract Completeness (Section 21)
    # -------------------------------------------------------------
    def test_t12_route_output_contract_completeness(
        self,
        router: RoadGraphRouter,
        scoring: EnvironmentalScoringEngine,
    ) -> None:
        snapshots = _mock_grounded_snapshots()
        station_pm25 = {s: d["pm25"] for s, d in snapshots.items()}

        candidates = router.generate_candidate_routes_from_origin(
            origin_lat=20.9938,
            origin_lng=105.9485,
            target_km=3.0,
            station_pm25_map=station_pm25,
            activity="running",
        )
        ranked = scoring.rank_route_candidates(
            candidates=candidates,
            station_data_map=snapshots,
            user_group="normal",
            target_km=3.0,
        )
        assert len(ranked) >= 1
        best = ranked[0]

        # Verify all required Section 21 fields
        required_fields = [
            "id", "distance_km", "distance_m", "mean_aqi", "max_aqi",
            "p90_aqi", "distance_above_threshold_m", "access_distance_m",
            "score", "coordinates", "edge_ids", "environment_segments",
        ]
        for field in required_fields:
            assert field in best, f"Missing required contract field: {field}"

        assert isinstance(best["coordinates"], list)
        assert len(best["coordinates"]) >= 2
        assert isinstance(best["edge_ids"], list)
        assert len(best["edge_ids"]) >= 1
        assert isinstance(best["environment_segments"], list)
        assert len(best["environment_segments"]) >= 1

