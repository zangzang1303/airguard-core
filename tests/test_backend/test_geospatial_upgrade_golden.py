import pytest

from backend.app.services.geospatial_agent_service import GeospatialAgentService
from backend.app.services.live_telemetry_engine import live_engine


@pytest.fixture
def agent_service() -> GeospatialAgentService:
    agent = GeospatialAgentService(telemetry_engine=live_engine)
    # Seed live stations with known data
    live_engine.update_station("S01", {"pm25": 45.0, "aqi": 124, "co2": 580.0, "noise_db": 62.0, "temperature": 29.5, "source": "simulator"})
    live_engine.update_station("S02", {"pm25": 32.0, "aqi": 93, "co2": 510.0, "noise_db": 54.0, "temperature": 28.0, "source": "simulator"})
    live_engine.update_station("S03", {"pm25": 12.0, "aqi": 35, "co2": 420.0, "noise_db": 45.0, "temperature": 25.0, "source": "simulator"})
    live_engine.update_station("S04", {"pm25": 15.0, "aqi": 42, "co2": 435.0, "noise_db": 46.0, "temperature": 26.0, "source": "simulator"})
    live_engine.update_station("S05", {"pm25": 20.0, "aqi": 68, "co2": 470.0, "noise_db": 49.0, "temperature": 27.0, "source": "simulator"})
    return agent


def test_road_hai_dang_recognition(agent_service: GeospatialAgentService):
    """Verify that Duong Hai Dang is recognized as an in-scope entity and correctly interpolated/resolved."""
    res = agent_service.process_query("Đường Hải Đăng không khí thế nào?")
    assert res["intent"] in {"get_location_environment", "get_noise_metric", "get_temperature_metric"}
    assert "Hải Đăng" in res["answer"]["summary"]
    assert res["map_actions"]
    assert any(a["type"] in {"highlight_area", "highlight_point", "add_annotation"} for a in res["map_actions"])
    assert "follow_up_actions" in res


def test_negation_indoor_routing(agent_service: GeospatialAgentService):
    """Verify that negation queries pivot to indoor activity without generating running route polylines."""
    res = agent_service.process_query("Ngoài chạy bộ tôi muốn hoạt động khác trong nhà")
    assert res["intent"] == "recommend_indoor_activity"
    assert "Trong nhà" in res["answer"]["summary"] or "trong nhà" in res["answer"]["summary"].lower()
    # Must NOT have highlight_route action
    assert not any(a["type"] == "highlight_route" for a in res["map_actions"])
    # Must have indoor venue highlight
    assert any(a["type"] == "highlight_point" for a in res["map_actions"])
    assert "follow_up_actions" in res


def test_worst_location_golden_response(agent_service: GeospatialAgentService):
    """Verify worst location returns clean 4-block structured answer, worst station S01, and cleaner alternative S03/S04."""
    res = agent_service.process_query("Khu nào đang ô nhiễm nhất?")
    assert res["intent"] == "find_worst_location"
    assert "S01" in res["answer"]["summary"]
    # Check that it identifies the cleaner alternative
    assert "S03" in res["answer"]["summary"] or "S04" in res["answer"]["summary"]
    assert any(a["type"] == "highlight_sensor" and a["severity"] == "danger" for a in res["map_actions"])
    assert "follow_up_actions" in res


def test_comparison_golden_response(agent_service: GeospatialAgentService):
    """Verify comparison query highlights both areas and selects the winner with higher air quality."""
    res = agent_service.process_query("So sánh San Hô và Hồ Ngọc Trai")
    assert res["intent"] == "compare_locations"
    assert "sạch hơn" in res["answer"]["summary"]
    assert len(res["candidates"]) == 2
    assert any(a["type"] == "highlight_area" and a["style"] == "recommended" for a in res["map_actions"])
    assert any(a["type"] == "highlight_area" and a["style"] == "caution" for a in res["map_actions"])
    assert "follow_up_actions" in res
