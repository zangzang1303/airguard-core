from __future__ import annotations

import pytest
from datetime import datetime, timezone

from backend.app.services.geospatial_agent_service import GeospatialAgentService
from backend.app.services.temporal_resolver import TemporalResolver
from backend.app.services.environmental_scoring import EnvironmentalScoringEngine
from backend.app.services.spatial_registry import SpatialRegistry
from backend.app.services.live_telemetry_engine import live_engine


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
    agent = GeospatialAgentService()

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
    agent = GeospatialAgentService()
    # User had clicked Hồ Ngọc Trai on the map and asks a follow-up: "Tối nay thì sao?"
    res = agent.process_query(
        message="Tối nay thì sao?",
        map_context={"selected_location": "Hồ Ngọc Trai", "selected_sensor": "S03"},
    )

    assert "Hồ Ngọc Trai" in res["answer"]["summary"]
    assert res["time_context"]["is_forecast"] is True
    assert any(a["type"] == "add_annotation" and "Hồ Ngọc Trai" in a["title"] for a in res["map_actions"])


def test_worst_location_intent():
    agent = GeospatialAgentService()
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
    agent = GeospatialAgentService()
    res = agent.process_query("Sapphire và Hồ Ngọc Trai chỗ nào tốt hơn?")
    assert res["intent"] == "compare_locations"
    assert "Sapphire" in res["answer"]["summary"] and "Hồ Ngọc Trai" in res["answer"]["summary"]
    assert any(a["type"] == "fit_bounds" for a in res["map_actions"])
    # Map actions must highlight both locations
    areas = [a for a in res["map_actions"] if a["type"] == "highlight_area"]
    assert len(areas) >= 2


def test_recommend_running_route_intent():
    agent = GeospatialAgentService()
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
    agent = GeospatialAgentService()
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


def test_indoor_pivot_when_air_is_hazardous():
    agent = GeospatialAgentService()
    # Scenario: Severe air pollution (AQI = 185, PM2.5 = 110 ug/m3)
    for s_id in ["S01", "S02", "S03", "S04", "S05"]:
        live_engine.update_station(s_id, {"pm25": 110.0, "aqi": 185, "co2": 1100.0, "noise_db": 75.0, "temperature": 32.0})

    res = agent.process_query("Tôi nên chạy bộ ở đâu bây giờ?")
    assert res["intent"] == "recommend_indoor_activity"
    assert "CẢNH BÁO" in res["answer"]["summary"] or "Không nên chạy bộ ngoài trời" in res["answer"]["summary"]
    # Must suggest indoor venues (e.g. Bể bơi 4 mùa / VinUni Sports Complex)
    assert "Bể bơi" in res["response"] or "VinUni" in res["response"] or "Trong nhà" in res["response"]
    assert any(a["type"] == "add_annotation" and ("🏊" in a["title"] or "Trong nhà" in a["badge"]) for a in res["map_actions"])
