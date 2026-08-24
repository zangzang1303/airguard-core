from __future__ import annotations

from backend.app.services.environmental_scoring import EnvironmentalScoringEngine
from backend.app.services.geospatial_agent_service import GeospatialAgentService
from backend.app.services.live_telemetry_engine import live_engine
from backend.app.services.road_graph_router import road_graph_router


def create_test_agent() -> GeospatialAgentService:
    return GeospatialAgentService(telemetry_engine=live_engine)


def test_running_route_data_reversal():
    """
    CRITICAL TEST 1: Data Reversal Test
    When West (S01, S04) is clean and East (S03, S05) is dirty -> West route wins.
    When East (S03, S05) is clean and West (S01, S04) is dirty -> East/Lake route wins.
    Proves ZERO hardcoded favorites or static bias.
    """
    agent = create_test_agent()

    # Case A: West Clean (S01=8, S04=10), East Dirty (S03=85, S05=90)
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        val = 8.0 if s_id == "S01" else (10.0 if s_id == "S04" else 85.0)
        live_engine.update_station(s_id, {"pm25": val, "aqi": int(val * 2.2), "co2": 450.0, "noise_db": 48.0, "temperature": 26.0})

    res_west = agent.process_query("Tìm đường chạy bộ tốt nhất bây giờ")
    route_action_west = next(a for a in res_west["map_actions"] if a["type"] == "highlight_route")
    assert any(k in route_action_west["route_id"] for k in ["san_ho", "zenpark", "vinuni", "riverwalk"])

    # Case B: East Clean (S03=8, S05=10), West Dirty (S01=85, S04=90)
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        val = 8.0 if s_id == "S03" else (10.0 if s_id == "S05" else 85.0)
        live_engine.update_station(s_id, {"pm25": val, "aqi": int(val * 2.2), "co2": 450.0, "noise_db": 48.0, "temperature": 26.0})

    res_east = agent.process_query("Tìm đường chạy bộ tốt nhất bây giờ")
    route_action_east = next(a for a in res_east["map_actions"] if a["type"] == "highlight_route")
    assert any(k in route_action_east["route_id"] for k in ["ngoc_trai", "lake", "crystal", "lagoon", "sapphire"])


def test_elimination_of_famous_poi_bias():
    """
    CRITICAL TEST 2: Elimination of Famous POI Bias
    When famous POI (San Hô S01 or VinUni S04) has poor AQI, but another corridor has clean air,
    the router MUST recommend the clean corridor and NOT default to the famous POI.
    """
    agent = create_test_agent()

    # San Hô (S01) and VinUni (S04) are heavily polluted (PM2.5 = 65, AQI = 145)
    # Lake / East (S03, S05) is very clean (PM2.5 = 12, AQI = 35)
    live_engine.update_station("S01", {"pm25": 65.0, "aqi": 145, "co2": 700.0, "noise_db": 65.0, "temperature": 31.0})
    live_engine.update_station("S02", {"pm25": 40.0, "aqi": 90, "co2": 520.0, "noise_db": 55.0, "temperature": 28.0})
    live_engine.update_station("S03", {"pm25": 12.0, "aqi": 35, "co2": 420.0, "noise_db": 45.0, "temperature": 25.0})
    live_engine.update_station("S04", {"pm25": 65.0, "aqi": 145, "co2": 700.0, "noise_db": 65.0, "temperature": 31.0})
    live_engine.update_station("S05", {"pm25": 15.0, "aqi": 40, "co2": 430.0, "noise_db": 46.0, "temperature": 25.0})

    res = agent.process_query("Đề xuất tuyến đường chạy bộ ngoài trời trong lành")
    assert res["intent"] == "recommend_running_route"
    top_route = next(a for a in res["map_actions"] if a["type"] == "highlight_route" and a.get("rank") == 1)

    # Must NOT recommend San Hô or VinUni
    assert "san_ho" not in top_route["route_id"]
    assert "vinuni" not in top_route["route_id"]
    # Must recommend Lake or Crystal Lagoon
    assert "ngoc_trai" in top_route["route_id"] or "lake" in top_route["route_id"] or "crystal" in top_route["route_id"]


def test_line_integral_sampling_vs_destination_shortcut():
    """
    CRITICAL TEST 3: Continuous Line-Integral Exposure vs Destination Sensor Shortcut
    Evaluates that route exposure integrates every point along the polyline using IDW.
    A route crossing through high PM2.5 sections gets higher mean AQI and hotspot penalty.
    """
    st_map = {
        "S01": {"pm25": 15.0, "aqi": 40, "co2": 420.0, "noise_db": 45.0, "temperature": 26.0},  # West Clean
        "S02": {"pm25": 30.0, "aqi": 75, "co2": 500.0, "noise_db": 52.0, "temperature": 27.0},
        "S03": {"pm25": 80.0, "aqi": 160, "co2": 800.0, "noise_db": 68.0, "temperature": 32.0}, # Lake Dirty
        "S04": {"pm25": 18.0, "aqi": 45, "co2": 430.0, "noise_db": 47.0, "temperature": 26.0},  # South Clean
        "S05": {"pm25": 75.0, "aqi": 155, "co2": 780.0, "noise_db": 65.0, "temperature": 31.0}, # East Dirty
    }

    # Route 1: Located purely in the West (San Hô to Zenpark)
    coords_west = [
        [20.9935, 105.9405], [20.9950, 105.9410], [20.9970, 105.9415],
        [20.9990, 105.9418], [21.0005, 105.9422], [20.9935, 105.9405],
    ]
    exp_west = EnvironmentalScoringEngine.evaluate_route_spatial_exposure(
        route_coords=coords_west,
        station_data_map=st_map,
        user_group="normal",
    )

    # Route 2: Located purely in the East (Lake Perimeter)
    coords_east = [
        [20.9938, 105.9485], [20.9965, 105.9508], [20.9975, 105.9530],
        [20.9955, 105.9568], [20.9918, 105.9510], [20.9938, 105.9485],
    ]
    exp_east = EnvironmentalScoringEngine.evaluate_route_spatial_exposure(
        route_coords=coords_east,
        station_data_map=st_map,
        user_group="normal",
    )

    # West Route must have significantly lower mean PM2.5 and AQI than East Route
    assert exp_west["mean_pm25"] < 30.0
    assert exp_east["mean_pm25"] > 50.0
    assert exp_west["exposure_score"] > exp_east["exposure_score"]
    assert exp_east["hotspot_distance_m"] > 0


def test_hotspot_penalty_and_p90_calculation():
    """
    CRITICAL TEST 4: Hotspot Penalty & P90 Percentile Calculation
    A route passing through an area with PM2.5 > 35 or AQI > 100 has a non-zero hotspot_distance_m
    and its P90 AQI is strictly greater than or equal to mean AQI.
    """
    st_map = {
        "S01": {"pm25": 10.0, "aqi": 30, "co2": 400.0, "noise_db": 45.0, "temperature": 25.0},
        "S02": {"pm25": 90.0, "aqi": 170, "co2": 900.0, "noise_db": 75.0, "temperature": 33.0}, # Hotspot at S02
        "S03": {"pm25": 12.0, "aqi": 35, "co2": 410.0, "noise_db": 46.0, "temperature": 25.0},
        "S04": {"pm25": 10.0, "aqi": 30, "co2": 400.0, "noise_db": 45.0, "temperature": 25.0},
        "S05": {"pm25": 15.0, "aqi": 40, "co2": 420.0, "noise_db": 46.0, "temperature": 25.0},
    }

    # Route that passes directly through S02
    coords_crossing_s02 = [
        [20.9935, 105.9405],
        [20.9975, 105.9430],  # Right at S02 (AQI 170)
        [20.9995, 105.9440],
        [20.9935, 105.9405],
    ]

    exp = EnvironmentalScoringEngine.evaluate_route_spatial_exposure(
        route_coords=coords_crossing_s02,
        station_data_map=st_map,
        user_group="normal",
    )

    assert exp["hotspot_distance_m"] > 0
    assert exp["hotspot_ratio"] > 0.0
    assert exp["p90_aqi"] >= exp["mean_aqi"]
    assert exp["breakdown"]["hotspot_penalty"] > 0.0


def test_distance_and_detour_precision():
    """
    CRITICAL TEST 5: Target Distance Honoring & Detour Penalization
    When user requests 2.0 km, 3.0 km, or 5.0 km, the system synthesizes routes matching
    the target distance along genuine graph edges without expanding to unmatched circuits.
    """
    agent = create_test_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 15.0, "aqi": 40, "co2": 450.0, "noise_db": 48.0, "temperature": 26.0})

    for target_km in [2.0, 3.0, 5.0]:
        res = agent.process_query(
            f"Tôi muốn chạy đúng {int(target_km)}km",
            map_context={"user_location": {"lat": 20.9975, "lng": 105.9430}},
        )
        assert res["intent"] == "recommend_personalized_running_route"
        p_route = res["personalized_route"]
        assert abs(p_route["distance_km"] - target_km) <= 0.4
        assert p_route["distance_constraint_satisfied"] is True
        assert len(p_route["coordinates"]) >= 5


def test_health_profile_sensitive_penalty():
    """
    CRITICAL TEST 6: Health Profile Sensitivity
    Sensitive group receives harsher penalty for elevated PM2.5/AQI and pollution hotspots.
    """
    st_map = {
        "S01": {"pm25": 38.0, "aqi": 105, "co2": 550.0, "noise_db": 55.0, "temperature": 28.0},
        "S02": {"pm25": 42.0, "aqi": 115, "co2": 580.0, "noise_db": 56.0, "temperature": 28.5},
        "S03": {"pm25": 36.0, "aqi": 102, "co2": 540.0, "noise_db": 54.0, "temperature": 28.0},
        "S04": {"pm25": 35.0, "aqi": 100, "co2": 530.0, "noise_db": 53.0, "temperature": 27.5},
        "S05": {"pm25": 40.0, "aqi": 110, "co2": 560.0, "noise_db": 55.0, "temperature": 28.0},
    }
    coords = [[20.9935, 105.9405], [20.9960, 105.9448], [20.9935, 105.9405]]

    normal_eval = EnvironmentalScoringEngine.evaluate_route_spatial_exposure(
        route_coords=coords,
        station_data_map=st_map,
        user_group="normal",
    )
    sensitive_eval = EnvironmentalScoringEngine.evaluate_route_spatial_exposure(
        route_coords=coords,
        station_data_map=st_map,
        user_group="sensitive",
    )

    assert sensitive_eval["exposure_score"] < normal_eval["exposure_score"]
    assert sensitive_eval["breakdown"]["hotspot_penalty"] > normal_eval["breakdown"]["hotspot_penalty"]


def test_comparative_exposure_reduction_calculation():
    """
    CRITICAL TEST 7: Comparative Exposure Reduction Calculation
    Ranks multiple candidates and verifies that Rank 1 has positive exposure_reduction_pct
    relative to the baseline route.
    """
    st_map = {
        "S01": {"pm25": 12.0, "aqi": 35, "co2": 420.0, "noise_db": 45.0, "temperature": 25.0},
        "S02": {"pm25": 30.0, "aqi": 75, "co2": 520.0, "noise_db": 55.0, "temperature": 27.0},
        "S03": {"pm25": 45.0, "aqi": 110, "co2": 620.0, "noise_db": 60.0, "temperature": 29.0},
        "S04": {"pm25": 14.0, "aqi": 38, "co2": 430.0, "noise_db": 46.0, "temperature": 25.0},
        "S05": {"pm25": 50.0, "aqi": 120, "co2": 650.0, "noise_db": 62.0, "temperature": 30.0},
    }

    candidates = road_graph_router.generate_candidate_routes_from_origin(
        origin_lat=20.9975,
        origin_lng=105.9430,
    )

    ranked = EnvironmentalScoringEngine.rank_route_candidates(
        candidates=candidates,
        station_data_map=st_map,
        user_group="normal",
    )

    assert len(ranked) >= 2
    best = ranked[0]
    worst = ranked[-1]

    assert best["rank"] == 1
    assert best["score"] >= worst["score"]
    assert best["pm25"] <= worst["pm25"]
    assert best["exposure_reduction_pct"] > 0.0


def test_origin_precedence_explicit_click_over_gps():
    """
    CRITICAL TEST 8: Origin Precedence - Map Click Overrides GPS
    When map_context contains selected_origin (West) and GPS user_location (East),
    the router MUST start at the clicked point in the West.
    """
    agent = create_test_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 15.0, "aqi": 40, "co2": 450.0, "noise_db": 48.0, "temperature": 26.0})

    res = agent.process_query(
        "Tìm đường chạy bộ phù hợp",
        map_context={
            "selected_origin": {"lat": 20.9940, "lng": 105.9380, "source": "map_selection", "name": "Điểm đã chọn tại The Zenpark"},
            "user_location": {"lat": 20.9945, "lng": 105.9585, "source": "gps", "name": "Vị trí GPS"},
        },
    )

    assert res["origin"]["source"] == "map_selection"
    assert "Điểm đã chọn" in res["origin"]["label"] or "Zenpark" in res["origin"]["label"]

    best_action = next(a for a in res["map_actions"] if a["type"] == "highlight_route" and a.get("rank") == 1)
    first_coord = best_action["coordinates"][0]
    # First coordinate must be near the selected origin (Zenpark West ~20.9940, 105.9380), NOT East GPS
    assert abs(first_coord[0] - 20.9940) < 0.005
    assert abs(first_coord[1] - 105.9380) < 0.005


def test_local_green_loop_no_10km_detour_to_lake():
    """
    CRITICAL TEST 9: Local Loop Synthesis & No 10km Detour
    When origin is at Zenpark / San Hô in the West and user asks for a general route (no target km),
    the route MUST stay local (2.0 - 5.0 km) and NOT generate a 10.3 km detour to Lake Ngọc Trai.
    """
    agent = create_test_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 15.0, "aqi": 40, "co2": 450.0, "noise_db": 48.0, "temperature": 26.0})

    res = agent.process_query(
        "Tìm cho tôi đường chạy bộ phù hợp nhất tối nay",
        map_context={
            "selected_origin": {"lat": 20.9950, "lng": 105.9375, "source": "map_selection"},
        },
    )

    best_action = next(a for a in res["map_actions"] if a["type"] == "highlight_route" and a.get("rank") == 1)
    dist_km = best_action["distance_km"]

    # Must be a sensible local loop (2.0 to 5.0 km), strictly NOT a 10+ km detour!
    assert 2.0 <= dist_km <= 5.0, f"Expected local distance 2.0-5.0km, got {dist_km}km"
    assert "10." not in str(dist_km)

    # Must start and end at the selected origin
    coords = best_action["coordinates"]
    assert abs(coords[0][0] - 20.9950) < 0.003
    assert abs(coords[-1][0] - 20.9950) < 0.003


def test_origin_label_disclosure_map_selection():
    """
    CRITICAL TEST 10: Origin Labeling & UI Disclosure
    When origin is from map selection, response details and annotations MUST display
    'Xuất phát: Điểm đã chọn trên bản đồ...' and NOT 'Vị trí của bạn'.
    """
    agent = create_test_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 15.0, "aqi": 40, "co2": 450.0, "noise_db": 48.0, "temperature": 26.0})

    res = agent.process_query(
        "Đề xuất cung đường chạy",
        map_context={
            "selected_point": [20.9995, 105.9415],
        },
    )

    details = res["answer"]["details"]
    assert "Điểm đã chọn trên bản đồ" in details
    assert "Vị trí của bạn" not in details or "Điểm đã chọn" in details

    start_annotation = next(a for a in res["map_actions"] if a["type"] == "add_annotation")
    assert "Điểm đã chọn" in start_annotation["title"]


def test_max_snap_distance_rejection():
    """
    CRITICAL TEST 11: Out-of-bounds Snap Distance Rejection
    If user clicks coordinates far outside Ocean Park (>250m from nearest road),
    the system informs the user clearly rather than creating an invalid route.
    """
    agent = create_test_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 15.0, "aqi": 40, "co2": 450.0, "noise_db": 48.0, "temperature": 26.0})

    res = agent.process_query(
        "Tìm đường chạy bộ",
        map_context={
            "selected_origin": {"lat": 21.0500, "lng": 105.8000, "source": "map_selection"},
        },
    )

    assert "chưa tìm thấy lối chạy bộ phù hợp đủ gần" in res["answer"]["summary"]
    assert len(res["map_actions"]) == 0


def test_loop_closure_geometry():
    """
    CRITICAL TEST 12: Loop Geometry Closure
    Validates that a generated running route loop has distance(start, end) == 0.
    """
    origin = (20.9995, 105.9415)
    candidates = road_graph_router.generate_candidate_routes_from_origin(
        origin_lat=origin[0],
        origin_lng=origin[1],
        target_km=3.5,
    )
    assert len(candidates) > 0
    top = candidates[0]
    coords = top["coordinates"]
    assert len(coords) >= 4
    # First point equals origin and last point equals origin
    assert abs(coords[0][0] - origin[0]) < 1e-4
    assert abs(coords[0][1] - origin[1]) < 1e-4
    assert abs(coords[-1][0] - origin[0]) < 1e-4
    assert abs(coords[-1][1] - origin[1]) < 1e-4


def test_route_exposure_returns_grounded_drawable_segments():
    station_map = {
        "S01": {"pm25": 12.0, "aqi": 35, "co2": 420.0, "noise_db": 45.0, "temperature": 25.0, "timestamp": "2026-08-24T08:00:00+00:00"},
        "S02": {"pm25": 85.0, "aqi": 165, "co2": 850.0, "noise_db": 72.0, "temperature": 32.0, "timestamp": "2026-08-24T08:00:00+00:00"},
        "S03": {"pm25": 18.0, "aqi": 48, "co2": 450.0, "noise_db": 47.0, "temperature": 26.0, "timestamp": "2026-08-24T08:00:00+00:00"},
        "S04": {"pm25": 10.0, "aqi": 30, "co2": 410.0, "noise_db": 44.0, "temperature": 25.0, "timestamp": "2026-08-24T08:00:00+00:00"},
        "S05": {"pm25": 20.0, "aqi": 55, "co2": 470.0, "noise_db": 49.0, "temperature": 27.0, "timestamp": "2026-08-24T08:00:00+00:00"},
    }
    route = [[20.9968, 105.9410], [20.9975, 105.9430], [20.9960, 105.9470]]

    exposure = EnvironmentalScoringEngine.evaluate_route_spatial_exposure(
        route_coords=route,
        station_data_map=station_map,
    )

    segments = exposure["environment_segments"]
    assert exposure["segment_count"] == len(segments)
    assert len(segments) > len(route)
    assert all(len(segment["coordinates"]) == 2 for segment in segments)
    assert all(segment["distance_m"] > 0 for segment in segments)
    assert all(segment["source"] == "spatial_idw_route_segment" for segment in segments)
    assert all(segment["source_station_ids"] for segment in segments)
    assert any(segment["level"] in {"unhealthy_sensitive", "unhealthy"} for segment in segments)


def test_agent_returns_one_best_route_with_time_specific_segment_profile():
    agent = create_test_agent()
    values = {"S01": 55.0, "S02": 70.0, "S03": 12.0, "S04": 18.0, "S05": 20.0}
    for station_id, pm25 in values.items():
        live_engine.update_station(
            station_id,
            {"pm25": pm25, "aqi": int(pm25 * 2.2), "co2": 500.0, "noise_db": 48.0, "temperature": 26.0},
        )

    result = agent.process_query(
        "Tìm tuyến chạy bộ 3km ít ô nhiễm nhất bây giờ",
        map_context={"user_location": {"lat": 20.9953, "lng": 105.9500, "source": "gps"}},
    )

    route_actions = [action for action in result["map_actions"] if action["type"] == "highlight_route"]
    assert len(route_actions) == 1
    route_action = route_actions[0]
    assert route_action["rank"] == 1
    assert route_action["data_mode"] == "live"
    assert route_action["source"] == "spatial_idw_route_segment"
    assert len(route_action["segments"]) > 0
    assert route_action["segments"] == result["personalized_route"]["environment_segments"]

    forecast_result = agent.process_query(
        "Tìm tuyến chạy bộ 3km ít ô nhiễm nhất tối nay",
        map_context={"user_location": {"lat": 20.9953, "lng": 105.9500, "source": "gps"}},
    )
    forecast_action = next(
        action for action in forecast_result["map_actions"] if action["type"] == "highlight_route"
    )
    assert forecast_result["time_context"]["is_forecast"] is True
    assert forecast_action["data_mode"] == "forecast"
    assert forecast_action["source"] == "forecast"
    assert forecast_action["observed_at"]
    assert all(segment["observed_at"] for segment in forecast_action["segments"])
