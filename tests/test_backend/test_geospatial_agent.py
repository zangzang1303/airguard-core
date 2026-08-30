from __future__ import annotations

import pytest

from backend.app.services.database import ServiceError
from backend.app.services.environmental_scoring import EnvironmentalScoringEngine
from backend.app.services.geospatial_agent_service import GeospatialAgentService
from backend.app.services.live_telemetry_engine import live_engine
from backend.app.services.temporal_resolver import TemporalResolver


def demo_agent() -> GeospatialAgentService:
    return GeospatialAgentService(telemetry_engine=live_engine)


def test_greeting_does_not_fall_through_to_environmental_recommendation():
    agent = demo_agent()

    result = agent.process_query(
        "Xin chào!",
        station_id="S01",
        map_context={"selected_sensor": "S01"},
    )

    assert result["intent"] in {"greeting", "social.greeting"}
    assert "Mình đây" in result["answer"]["summary"]
    assert result["evidence"] == []
    assert result["map_actions"] == []
    assert result["used_tools"] == []
    assert "time_context" not in result


def test_unknown_chat_does_not_fall_through_to_environmental_recommendation():
    agent = demo_agent()

    result = agent.process_query("ừm... abcxyz")

    assert result["intent"] in {"clarification", "conversation.unknown"}
    assert result["evidence"] == []
    assert result["map_actions"] == []
    assert "Bạn muốn mình kiểm tra" in result["response"] or "AQI" in result["response"]


def test_temporal_resolver_patterns():
    # 1. Live queries
    res_now = TemporalResolver.resolve("Chất lượng không khí hiện tại thế nào?")
    assert res_now["type"] == "live"
    assert res_now["is_forecast"] is False
    assert res_now["forecast_hour"] == 0

    # 2. Forecast queries: "tối nay"
    res_tonight = TemporalResolver.resolve("Tối nay tôi có thể chạy bộ không?")
    assert res_tonight["type"] == "forecast"
    assert res_tonight["is_forecast"] is True
    assert res_tonight["forecast_hour"] >= 1
    assert "tối nay" in res_tonight["label"].lower()

    # 3. Forecast queries: "chiều nay"
    res_afternoon = TemporalResolver.resolve("Chiều nay thời tiết thế nào?")
    assert res_afternoon["type"] == "forecast"
    assert res_afternoon["is_forecast"] is True

    # 4. Offset: "2h nữa"
    res_offset = TemporalResolver.resolve("Sau 2 tiếng nữa không khí ra sao?")
    assert res_offset["type"] == "forecast"
    assert res_offset["forecast_hour"] == 2


def test_environmental_scoring_weights():
    cand = {"pm25": 15.0, "aqi": 45, "temperature": 25.0, "noise_db": 50.0}
    score_res = EnvironmentalScoringEngine.score_candidate(cand, activity="running")

    assert score_res["score"] >= 80.0
    assert score_res["tier"] == "recommended"

    # Bad environment candidate
    bad_cand = {"pm25": 90.0, "aqi": 180, "temperature": 38.0, "noise_db": 85.0}
    bad_res = EnvironmentalScoringEngine.score_candidate(bad_cand, activity="running")
    assert bad_res["score"] < 40.0
    assert bad_res["tier"] in {"caution", "avoid"}


def test_dynamic_ranking_not_hardcoded():
    """
    CRITICAL PROOF TEST:
    Changing the underlying station telemetry flips the AI Agent's recommendation and map actions,
    proving zero hardcoding of favorite locations.
    """
    agent = demo_agent()

    # Scenario A: S04 (VinUni) is cleanest (PM2.5 = 10), S03 (Hồ Ngọc Trai) is dirty (PM2.5 = 90)
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        val = 10.0 if s_id == "S04" else (90.0 if s_id == "S03" else 45.0)
        live_engine.update_station(s_id, {"pm25": val, "aqi": int(val * 2.2), "co2": 550.0, "noise_db": 50.0, "temperature": 27.0})

    res_a = agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")
    assert "VinUni" in res_a["answer"]["summary"] or "route_vinuni" in str(res_a["map_actions"])
    # First highlight action must highlight VinUni
    highlight_a = next(a for a in res_a["map_actions"] if a["type"] in {"highlight_route", "highlight_area"})
    assert highlight_a.get("route_id") == "route_vinuni_circuit" or highlight_a.get("area_id") == "poi_vinuni"
    assert highlight_a["style"] == "recommended"

    # Scenario B: Now S03 (Hồ Ngọc Trai) becomes cleanest (PM2.5 = 8), S04 (VinUni) becomes dirty (PM2.5 = 95)
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        val = 8.0 if s_id == "S03" else (95.0 if s_id == "S04" else 50.0)
        live_engine.update_station(s_id, {"pm25": val, "aqi": int(val * 2.2), "co2": 550.0, "noise_db": 48.0, "temperature": 26.0})

    res_b = agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")
    assert "Hồ Ngọc Trai" in res_b["answer"]["summary"] or "route_ngoc_trai_loop" in str(res_b["map_actions"])
    highlight_b = next(a for a in res_b["map_actions"] if a["type"] in {"highlight_route", "highlight_area"})
    assert highlight_b.get("route_id") == "route_ngoc_trai_loop" or highlight_b.get("area_id") == "poi_ngoc_trai_lake"
    assert highlight_b["style"] == "recommended"


def test_follow_up_map_context_retention():
    agent = demo_agent()
    # User had clicked Hồ Ngọc Trai on the map and asks a follow-up: "Tối nay thì sao?"
    res = agent.process_query(
        message="Tối nay thì sao?",
        map_context={"selected_location": "Hồ Ngọc Trai", "selected_sensor": "S03"},
    )

    assert "Hồ Ngọc Trai" in res["answer"]["summary"]
    assert res["time_context"]["is_forecast"] is True
    assert any(a["type"] == "add_annotation" and "Hồ Ngọc Trai" in a["title"] for a in res["map_actions"])


def test_worst_location_intent():
    agent = demo_agent()
    # Set S01 to highest pollution
    live_engine.update_station("S01", {"pm25": 115.0, "aqi": 195, "co2": 1200.0, "noise_db": 82.0, "temperature": 34.0})
    for s in ["S02", "S03", "S04", "S05"]:
        live_engine.update_station(s, {"pm25": 25.0, "aqi": 70, "co2": 500.0, "noise_db": 50.0, "temperature": 28.0})

    res = agent.process_query("Khu nào đang ô nhiễm nhất?")
    assert res["intent"] == "find_worst_location"
    assert "S01" in res["answer"]["summary"] or "Đa Tốn" in res["answer"]["summary"] or "poi_san_ho" in str(res["map_actions"])
    # Map action must have danger highlight and fly_to
    assert any(a["type"] == "highlight_sensor" and a["severity"] == "danger" for a in res["map_actions"])
    assert any(a["type"] == "fly_to" for a in res["map_actions"])


def test_comparison_intent():
    agent = demo_agent()
    res = agent.process_query("Sapphire và Hồ Ngọc Trai chỗ nào tốt hơn?")
    assert res["intent"] == "compare_locations"
    assert "Sapphire" in res["answer"]["summary"] and "Hồ Ngọc Trai" in res["answer"]["summary"]
    assert any(a["type"] == "fit_bounds" for a in res["map_actions"])
    # Map actions must highlight both locations
    areas = [a for a in res["map_actions"] if a["type"] == "highlight_area"]
    assert len(areas) >= 2


def test_explicit_station_uses_physical_sensor_coordinates_for_map_actions():
    agent = demo_agent()

    res = agent.process_query("Chất lượng không khí tại S01 hiện thế nào?")

    assert res["intent"] == "get_location_environment"
    assert res["target_station"] == "S01"
    for action in res["map_actions"]:
        if action["type"] in {"highlight_point", "add_annotation", "fly_to"}:
            assert action["lat"] == pytest.approx(21.0008)
            assert action["lng"] == pytest.approx(105.9428)


def test_explicit_station_comparison_uses_both_physical_sensor_coordinates():
    agent = demo_agent()

    res = agent.process_query("So sánh S01 và S02")

    assert res["intent"] == "compare_locations"
    highlights = [action for action in res["map_actions"] if action["type"] == "highlight_area"]
    assert {(action["lat"], action["lng"]) for action in highlights} == {
        (21.0008, 105.9428),
        (20.9975, 105.9430),
    }


def test_consecutive_station_ids_do_not_be_interpreted_as_poi_aliases():
    agent = demo_agent()
    conversation_id = "test-consecutive-station-ids"
    expected_coordinates = {
        "S01": (21.0008, 105.9428),
        "S02": (20.9975, 105.9430),
        "S05": (20.9910, 105.9560),
    }

    for station_id, (latitude, longitude) in expected_coordinates.items():
        res = agent.process_query(station_id, conversation_id=conversation_id)
        assert res["intent"] == "get_location_environment"
        fly_to = next(action for action in res["map_actions"] if action["type"] == "fly_to")
        assert fly_to["lat"] == pytest.approx(latitude)
        assert fly_to["lng"] == pytest.approx(longitude)


def test_contextual_three_station_comparison_uses_last_three_explicit_stations():
    agent = demo_agent()
    conversation_id = "test-contextual-three-station-comparison"
    for station_id in ("S01", "S02", "S03"):
        agent.process_query(station_id, conversation_id=conversation_id)

    res = agent.process_query("so sánh 3 trạm", conversation_id=conversation_id)

    assert res["intent"] == "compare_stations"
    assert [item["station_id"] for item in res["candidates"]] == ["S01", "S02", "S03"]
    assert len([action for action in res["map_actions"] if action["type"] == "highlight_area"]) == 3


def test_recommend_running_route_intent():
    agent = demo_agent()
    # Scenario: Ask for running routes tonight
    res = agent.process_query("Tôi muốn tìm đoạn đường phù hợp để chạy bộ nhất tối nay")
    assert res["intent"] == "recommend_running_route"
    assert res["time_context"]["is_forecast"] is True

    # Must contain highlight_route action
    route_actions = [a for a in res["map_actions"] if a["type"] == "highlight_route"]
    assert len(route_actions) >= 1

    best_route = route_actions[0]
    assert "coordinates" in best_route
    assert len(best_route["coordinates"]) >= 4
    assert best_route["distance_km"] > 0
    assert best_route["style"] == "recommended"

    # Must have start flag annotation
    assert any(a["type"] == "add_annotation" and "🚩 Xuất phát" in a["title"] for a in res["map_actions"])
    assert any(a["type"] == "fit_bounds" for a in res["map_actions"])


def test_personalized_route_from_user_location_and_target_distance():
    agent = demo_agent()
    # Scenario: User is at Sapphire and wants to run 5km
    map_context = {
        "user_location": {"lat": 20.9975, "lng": 105.9430},
        "selected_location": "poi_sapphire",
    }
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0})

    res = agent.process_query("Tôi đang ở Sapphire muốn chạy 5km", map_context=map_context)
    assert res["intent"] == "recommend_personalized_running_route"
    assert "5" in str(res["answer"]["summary"]) or "5" in str(res["response"])
    assert res["personalized_route"]["distance_km"] >= 4.0

    # Must have highlight_route starting at user's coordinate
    route_action = next(a for a in res["map_actions"] if a["type"] == "highlight_route")
    first_coord = route_action["coordinates"][0]
    assert abs(first_coord[0] - 20.9975) < 0.001
    assert abs(first_coord[1] - 105.9430) < 0.001


def test_running_distance_follow_up_adjusts_route_instead_of_clarifying():
    agent = demo_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(
            s_id,
            {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0},
        )

    res = agent.process_query(
        "Tôi chỉ muốn chạy 2km thôi",
        map_context={"user_location": {"lat": 20.9975, "lng": 105.9430}},
    )

    assert res["intent"] == "recommend_personalized_running_route"
    route_action = next(action for action in res["map_actions"] if action["type"] == "highlight_route")
    assert route_action["distance_km"] == 2.0
    assert res["personalized_route"]["planning_method"] == "environment_weighted_graph_round_trip"
    assert any(action["type"] == "highlight_route" for action in res["map_actions"])


def test_dynamic_route_planner_honors_three_km_target_without_lake_loop_expansion():
    agent = demo_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(
            s_id,
            {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0},
        )

    res = agent.process_query(
        "Tôi chỉ muốn chạy 3km thôi",
        map_context={"user_location": {"lat": 20.9975, "lng": 105.9430}},
    )

    route = res["personalized_route"]
    assert route["target_requested_km"] == 3.0
    assert route["distance_km"] == 3.0
    assert route["distance_constraint_satisfied"] is True
    assert route["laps"] == 0


def test_domain_query_fails_closed_without_grounded_station_snapshots():
    agent = GeospatialAgentService()

    with pytest.raises(ServiceError) as exc_info:
        agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")

    assert exc_info.value.code == "geospatial_station_data_unavailable"
    assert exc_info.value.status_code == 503


def test_uc03_least_polluted_three_km_query_is_routed_as_personalized_route():
    agent = demo_agent()
    for station_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(
            station_id,
            {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0},
        )

    result = agent.process_query(
        "Tôi muốn chạy 3km, tìm tuyến đường ít ô nhiễm nhất",
        map_context={"user_location": {"lat": 20.9975, "lng": 105.9430}},
    )

    assert result["intent"] == "recommend_personalized_running_route"
    assert result["personalized_route"]["target_requested_km"] == 3.0
    assert any(action["type"] == "highlight_route" for action in result["map_actions"])


def test_indoor_pivot_when_air_is_hazardous():
    agent = demo_agent()
    # Scenario: Severe air pollution (AQI = 185, PM2.5 = 110 ug/m3)
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 110.0, "aqi": 185, "co2": 1100.0, "noise_db": 75.0, "temperature": 32.0})

    res = agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")
    assert res["intent"] == "recommend_indoor_activity"
    assert "CẢNH BÁO" in res["answer"]["summary"] or "Không nên chạy bộ ngoài trời" in res["answer"]["summary"]
    # Must suggest indoor venues (e.g. Bể bơi 4 mùa / VinUni Sports Complex)
    assert "Bể bơi" in res["response"] or "VinUni" in res["response"] or "Trong nhà" in res["response"]
    assert any(a["type"] == "add_annotation" and ("🏊" in a["title"] or "Trong nhà" in a["badge"]) for a in res["map_actions"])


def test_rain_inquiry_explains_sensor_scope_and_gives_microclimate_fallback():
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 1.0, "aqi": 4, "co2": 350.0, "noise_db": 30.0, "temperature": 25.0})

    res = agent.process_query("Bây giờ ở san hô có mưa hay không")
    assert res["intent"] == "unsupported_precipitation_weather"
    assert "chưa trang bị cảm biến đo lượng mưa" in res["answer"]["summary"] or "ngoài phạm vi" in res["answer"]["summary"]
    assert "San Hô" in res["response"]
    assert "25.0°C" in res["response"] or "25°C" in res["response"]
    assert any(a["type"] == "highlight_point" and "San Hô" in a.get("name", "") for a in res["map_actions"])


def test_out_of_scope_medical_and_dining_questions_handled_transparently():
    agent = demo_agent()

    res_med = agent.process_query("Tôi bị đau đầu thì nên uống thuốc gì?")
    assert res_med["intent"] == "out_of_scope"
    assert "ngoài phạm vi" in res_med["answer"]["summary"]

    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        val = 8.0 if s_id == "S03" else (95.0 if s_id == "S04" else 50.0)
        live_engine.update_station(s_id, {"pm25": val, "aqi": int(val * 2.2), "co2": 550.0, "noise_db": 48.0, "temperature": 26.0})

    res_b = agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")
    assert "Hồ Ngọc Trai" in res_b["answer"]["summary"] or "route_ngoc_trai_loop" in str(res_b["map_actions"])
    highlight_b = next(a for a in res_b["map_actions"] if a["type"] in {"highlight_route", "highlight_area"})
    assert highlight_b.get("route_id") == "route_ngoc_trai_loop" or highlight_b.get("area_id") == "poi_ngoc_trai_lake"
    assert highlight_b["style"] == "recommended"


def test_follow_up_map_context_retention():
    agent = demo_agent()
    # User had clicked Hồ Ngọc Trai on the map and asks a follow-up: "Tối nay thì sao?"
    res = agent.process_query(
        message="Tối nay thì sao?",
        map_context={"selected_location": "Hồ Ngọc Trai", "selected_sensor": "S03"},
    )

    assert "Hồ Ngọc Trai" in res["answer"]["summary"]
    assert res["time_context"]["is_forecast"] is True
    assert any(a["type"] == "add_annotation" and "Hồ Ngọc Trai" in a["title"] for a in res["map_actions"])


def test_worst_location_intent():
    agent = demo_agent()
    # Set S01 to highest pollution
    live_engine.update_station("S01", {"pm25": 115.0, "aqi": 195, "co2": 1200.0, "noise_db": 82.0, "temperature": 34.0})
    for s in ["S02", "S03", "S04", "S05"]:
        live_engine.update_station(s, {"pm25": 25.0, "aqi": 70, "co2": 500.0, "noise_db": 50.0, "temperature": 28.0})

    res = agent.process_query("Khu nào đang ô nhiễm nhất?")
    assert res["intent"] == "find_worst_location"
    assert "S01" in res["answer"]["summary"] or "Đa Tốn" in res["answer"]["summary"] or "poi_san_ho" in str(res["map_actions"])
    # Map action must have danger highlight and fly_to
    assert any(a["type"] == "highlight_sensor" and a["severity"] == "danger" for a in res["map_actions"])
    assert any(a["type"] == "fly_to" for a in res["map_actions"])


def test_comparison_intent():
    agent = demo_agent()
    res = agent.process_query("Sapphire và Hồ Ngọc Trai chỗ nào tốt hơn?")
    assert res["intent"] == "compare_locations"
    assert "Sapphire" in res["answer"]["summary"] and "Hồ Ngọc Trai" in res["answer"]["summary"]
    assert any(a["type"] == "fit_bounds" for a in res["map_actions"])
    # Map actions must highlight both locations
    areas = [a for a in res["map_actions"] if a["type"] == "highlight_area"]
    assert len(areas) >= 2


def test_recommend_running_route_intent():
    agent = demo_agent()
    # Scenario: Ask for running routes tonight
    res = agent.process_query("Tôi muốn tìm đoạn đường phù hợp để chạy bộ nhất tối nay")
    assert res["intent"] == "recommend_running_route"
    assert res["time_context"]["is_forecast"] is True

    # Must contain highlight_route action
    route_actions = [a for a in res["map_actions"] if a["type"] == "highlight_route"]
    assert len(route_actions) >= 1

    best_route = route_actions[0]
    assert "coordinates" in best_route
    assert len(best_route["coordinates"]) >= 4
    assert best_route["distance_km"] > 0
    assert best_route["style"] == "recommended"

    # Must have start flag annotation
    assert any(a["type"] == "add_annotation" and "🚩 Xuất phát" in a["title"] for a in res["map_actions"])
    assert any(a["type"] == "fit_bounds" for a in res["map_actions"])


def test_personalized_route_from_user_location_and_target_distance():
    agent = demo_agent()
    # Scenario: User is at Sapphire and wants to run 5km
    map_context = {
        "user_location": {"lat": 20.9975, "lng": 105.9430},
        "selected_location": "poi_sapphire",
    }
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0})

    res = agent.process_query("Tôi đang ở Sapphire muốn chạy 5km", map_context=map_context)
    assert res["intent"] == "recommend_personalized_running_route"
    assert "5" in str(res["answer"]["summary"]) or "5" in str(res["response"])
    assert res["personalized_route"]["distance_km"] >= 4.0

    # Must have highlight_route starting at user's coordinate
    route_action = next(a for a in res["map_actions"] if a["type"] == "highlight_route")
    first_coord = route_action["coordinates"][0]
    assert abs(first_coord[0] - 20.9975) < 0.001
    assert abs(first_coord[1] - 105.9430) < 0.001


def test_running_distance_follow_up_adjusts_route_instead_of_clarifying():
    agent = demo_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(
            s_id,
            {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0},
        )

    res = agent.process_query(
        "Tôi chỉ muốn chạy 2km thôi",
        map_context={"user_location": {"lat": 20.9975, "lng": 105.9430}},
    )

    assert res["intent"] == "recommend_personalized_running_route"
    route_action = next(action for action in res["map_actions"] if action["type"] == "highlight_route")
    assert route_action["distance_km"] == 2.0
    assert res["personalized_route"]["planning_method"] == "environment_weighted_graph_round_trip"
    assert any(action["type"] == "highlight_route" for action in res["map_actions"])


def test_dynamic_route_planner_honors_three_km_target_without_lake_loop_expansion():
    agent = demo_agent()
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(
            s_id,
            {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0},
        )

    res = agent.process_query(
        "Tôi chỉ muốn chạy 3km thôi",
        map_context={"user_location": {"lat": 20.9975, "lng": 105.9430}},
    )

    route = res["personalized_route"]
    assert route["target_requested_km"] == 3.0
    assert route["distance_km"] == 3.0
    assert route["distance_constraint_satisfied"] is True
    assert route["laps"] == 0


def test_domain_query_fails_closed_without_grounded_station_snapshots():
    agent = GeospatialAgentService()

    with pytest.raises(ServiceError) as exc_info:
        agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")

    assert exc_info.value.code == "geospatial_station_data_unavailable"
    assert exc_info.value.status_code == 503


def test_uc03_least_polluted_three_km_query_is_routed_as_personalized_route():
    agent = demo_agent()
    for station_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(
            station_id,
            {"pm25": 18.0, "aqi": 45, "co2": 500.0, "noise_db": 48.0, "temperature": 26.0},
        )

    result = agent.process_query(
        "Tôi muốn chạy 3km, tìm tuyến đường ít ô nhiễm nhất",
        map_context={"user_location": {"lat": 20.9975, "lng": 105.9430}},
    )

    assert result["intent"] == "recommend_personalized_running_route"
    assert result["personalized_route"]["target_requested_km"] == 3.0
    assert any(action["type"] == "highlight_route" for action in result["map_actions"])


def test_indoor_pivot_when_air_is_hazardous():
    agent = demo_agent()
    # Scenario: Severe air pollution (AQI = 185, PM2.5 = 110 ug/m3)
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 110.0, "aqi": 185, "co2": 1100.0, "noise_db": 75.0, "temperature": 32.0})

    res = agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")
    assert res["intent"] == "recommend_indoor_activity"
    assert "CẢNH BÁO" in res["answer"]["summary"] or "Không nên chạy bộ ngoài trời" in res["answer"]["summary"]
    # Must suggest indoor venues (e.g. Bể bơi 4 mùa / VinUni Sports Complex)
    assert "Bể bơi" in res["response"] or "VinUni" in res["response"] or "Trong nhà" in res["response"]
    assert any(a["type"] == "add_annotation" and ("🏊" in a["title"] or "Trong nhà" in a["badge"]) for a in res["map_actions"])


def test_rain_inquiry_explains_sensor_scope_and_gives_microclimate_fallback():
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 1.0, "aqi": 4, "co2": 350.0, "noise_db": 30.0, "temperature": 25.0})

    res = agent.process_query("Bây giờ ở san hô có mưa hay không")
    assert res["intent"] == "unsupported_precipitation_weather"
    assert "chưa trang bị cảm biến đo lượng mưa" in res["answer"]["summary"] or "ngoài phạm vi" in res["answer"]["summary"]
    assert "San Hô" in res["response"]
    assert "25.0°C" in res["response"] or "25°C" in res["response"]
    assert any(a["type"] == "highlight_point" and "San Hô" in a.get("name", "") for a in res["map_actions"])


def test_out_of_scope_medical_and_dining_questions_handled_transparently():
    agent = demo_agent()

    res_med = agent.process_query("Tôi bị đau đầu thì nên uống thuốc gì?")
    assert res_med["intent"] == "out_of_scope"
    assert "ngoài phạm vi" in res_med["answer"]["summary"]

    res_dining = agent.process_query("Ở đây có quán phở nào ngon không?")
    assert res_dining["intent"] == "out_of_scope"
    assert "ngoài phạm vi" in res_dining["answer"]["summary"]


def test_specific_noise_and_temp_questions():
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 10.0, "aqi": 30, "co2": 450.0, "noise_db": 42.0, "temperature": 26.5})

    res_noise = agent.process_query("Độ ồn ở công viên san hô thế nào?")
    assert res_noise["intent"] == "get_noise_metric"
    assert "42.0 dB" in res_noise["response"] or "42 dB" in res_noise["response"]

    res_temp = agent.process_query("Nhiệt độ ở công viên san hô bao nhiêu độ?")
    assert res_temp["intent"] == "get_temperature_metric"
    assert "26.5°C" in res_temp["response"] or "26.5" in res_temp["response"]


def test_an_dao_location_grounding_overrides_active_map_selection():
    """
    Test that explicit user inquiry for 'An Đào' resolves to An Đào POI with IDW interpolation
    and strictly overrides any existing active map selection (e.g. Công viên San Hô).
    """
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 12.0, "aqi": 38, "co2": 420.0, "noise_db": 44.0, "temperature": 25.0})
    live_engine.update_station("S02", {"pm25": 18.0, "aqi": 52, "co2": 480.0, "noise_db": 48.0, "temperature": 26.0})

    # User currently has Công viên San Hô selected on map, but explicitly asks for An Đào
    res = agent.process_query(
        "chất lượng không khí tại an đào",
        map_context={"selected_location": "poi_san_ho_park", "selected_sensor": "S01"},
    )

    assert res["intent"] == "get_location_environment"
    assert "An Đào" in res["answer"]["summary"]
    assert "San Hô" not in res["answer"]["summary"]
    assert res["target_location"] == "An Đào"
    assert res["resolved_location"]["id"] == "poi_an_dao"
    assert res["resolved_location"]["is_interpolated"] is True
    assert "S01" in res["resolved_location"]["source_sensors"] or "S02" in res["resolved_location"]["source_sensors"]

    # Check that map actions target An Đào coordinates (20.9995, 105.9415)
    fly_to_action = next((a for a in res["map_actions"] if a["type"] == "fly_to"), None)
    assert fly_to_action is not None
    assert abs(fly_to_action["lat"] - 20.9995) < 0.001
    assert abs(fly_to_action["lng"] - 105.9415) < 0.001

    # Check evidence structure
    assert any(e.get("is_interpolated") is True and e.get("target_location") == "An Đào" for e in res["evidence"])


def test_deictic_query_without_explicit_name_uses_map_selection():
    """
    Test that queries like 'ở đây thế nào?' or 'chỗ này thì sao?' respect map selection.
    """
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 12.0, "aqi": 38, "co2": 420.0, "noise_db": 44.0, "temperature": 25.0})

    res = agent.process_query(
        "ở đây thế nào?",
        map_context={"selected_location": "poi_san_ho_park", "selected_sensor": "S01"},
    )
    assert res["intent"] == "get_location_environment"
    assert "San Hô" in res["answer"]["summary"]
    assert res["resolved_location"]["id"] == "poi_san_ho_park"


def test_explicit_short_station_id_overrides_selected_poi_label():
    """S1 means telemetry station S01, even when San Hô is selected on the map."""
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 12.0, "aqi": 38, "co2": 420.0, "noise_db": 44.0, "temperature": 25.0})

    res = agent.process_query(
        "chất lượng không khí tại trạm S1 thế nào?",
        map_context={"selected_location": "poi_san_ho_park", "selected_sensor": "S01"},
    )

    assert res["intent"] == "get_location_environment"
    assert "Trạm S01" in res["answer"]["summary"]
    assert "San Hô" not in res["answer"]["summary"]
    assert res["target_station"] == "S01"


def test_unknown_location_outside_ocean_park_fails_closed():
    """
    Test that queries for unknown locations outside Ocean Park 1 (e.g. ABCXYZ)
    return unknown_location intent and do NOT silently return active map selection.
    """
    agent = demo_agent()
    res = agent.process_query(
        "chất lượng không khí tại ABCXYZ",
        map_context={"selected_location": "poi_san_ho_park", "selected_sensor": "S01"},
    )
    assert res["intent"] == "unknown_location"
    assert "chưa xác định được địa điểm “Abcxyz”" in res["answer"]["summary"] or "chưa xác định được địa điểm" in res["answer"]["summary"]
    assert "Vinhomes Ocean Park 1" in res["answer"]["details"]
    assert res["map_actions"] == [{"type": "clear_ai_layer"}]


def test_comparison_between_interpolated_and_physical_poi():
    """
    Test comparing an interpolated subdivision (An Đào) and a physical sensor POI (Hồ Ngọc Trai).
    """
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 10.0, "aqi": 35, "co2": 400.0, "noise_db": 40.0, "temperature": 25.0})
    live_engine.update_station("S02", {"pm25": 12.0, "aqi": 40, "co2": 420.0, "noise_db": 42.0, "temperature": 25.5})
    live_engine.update_station("S03", {"pm25": 50.0, "aqi": 115, "co2": 750.0, "noise_db": 58.0, "temperature": 29.0})

    res = agent.process_query("So sánh chất lượng không khí giữa An Đào và Hồ Ngọc Trai")
    assert res["intent"] == "compare_locations"
    assert "An Đào" in res["answer"]["summary"]
    assert "Hồ Ngọc Trai" in res["answer"]["summary"]
    # An Đào is cleaner (AQI ~ 37 vs S03 AQI 115)
    assert "An Đào" in res["answer"]["summary"]
    assert any(c["name"] == "An Đào" for c in res["candidates"])
    assert any(c["name"] == "Hồ Ngọc Trai" for c in res["candidates"])


def test_ocean_park_area_overview_intent():
    """
    Test asking general questions about Ocean Park 1 / toàn khu / OCP1
    resolves to environment.overview intent instead of unknown location error.
    """
    agent = demo_agent()
    live_engine.update_station("S01", {"pm25": 10.0, "aqi": 35, "co2": 400.0, "noise_db": 40.0, "temperature": 25.0})
    live_engine.update_station("S02", {"pm25": 12.0, "aqi": 40, "co2": 420.0, "noise_db": 42.0, "temperature": 25.5})
    live_engine.update_station("S03", {"pm25": 50.0, "aqi": 115, "co2": 750.0, "noise_db": 58.0, "temperature": 29.0})

    queries = [
        "Chất lượng không khí hiện tại ở Ocean Park 1?",
        "Chất lượng không khí ở Ocean Park 1",
        "Không khí tại Vinhomes Ocean Park 1 thế nào?",
        "Không khí toàn khu hiện tại thế nào?",
    ]

    for q in queries:
        res = agent.process_query(q)
        assert res["intent"] == "environment.overview", f"Failed on query: {q}"
        assert "Ocean Park 1" in res["answer"]["headline"]
        assert any(a["type"] == "show_heatmap" for a in res["map_actions"])

