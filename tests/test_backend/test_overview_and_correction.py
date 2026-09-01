"""Dedicated Test Suite for Area Overview Intent, Scope Resolver, and Context Correction.

Tests requirements from docs/AirGuard_Task_Fix_Overview_Intent_Context_Scope.md:
- T01: Overview intent & OCP1 scope detection
- T02: Ranking best location ("Khu nào sạch nhất?")
- T03: Ranking worst location ("Khu nào ô nhiễm nhất?")
- T04: Single location inquiry ("Không khí VinUni thế nào?")
- T05: Conversational correction ("Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1")
- T06: Overview map action validation (fit whole OCP1 bounds, show all 5 stations, no single POI zoom)
- T07: Context override (VinUni -> "toàn khu thì sao?")
- Technical leakage prevention.
"""

import pytest

from backend.app.services.conversation_state_manager import conversation_state_manager
from backend.app.services.geospatial_agent_service import GeospatialAgentService
from backend.app.services.response_composer import ResponseValidator


@pytest.fixture
def mock_snapshots():
    return {
        "S01": {
            "station_id": "S01",
            "name": "Trục Đa Tốn phía Tây Bắc",
            "latitude": 21.0008,
            "longitude": 105.9428,
            "pm25": 56.0,
            "aqi": 146,
            "co2": 720.0,
            "noise_db": 68.0,
            "temperature": 32.0,
            "status": "online",
            "freshness": "fresh",
            "updated_at": "2026-08-27T14:00:00Z",
            "source": "simulator",
        },
        "S02": {
            "station_id": "S02",
            "name": "Khu căn hộ Sapphire",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "pm25": 24.0,
            "aqi": 76,
            "co2": 520.0,
            "noise_db": 54.0,
            "temperature": 28.0,
            "status": "online",
            "freshness": "fresh",
            "updated_at": "2026-08-27T14:00:00Z",
            "source": "simulator",
        },
        "S03": {
            "station_id": "S03",
            "name": "Ven Hồ Ngọc Trai",
            "latitude": 20.9953,
            "longitude": 105.9500,
            "pm25": 18.0,
            "aqi": 63,
            "co2": 460.0,
            "noise_db": 49.0,
            "temperature": 27.5,
            "status": "online",
            "freshness": "fresh",
            "updated_at": "2026-08-27T14:00:00Z",
            "source": "simulator",
        },
        "S04": {
            "station_id": "S04",
            "name": "Khuôn viên VinUni",
            "latitude": 20.9898,
            "longitude": 105.9467,
            "pm25": 14.0,
            "aqi": 53,
            "co2": 440.0,
            "noise_db": 46.0,
            "temperature": 26.8,
            "status": "online",
            "freshness": "fresh",
            "updated_at": "2026-08-27T14:00:00Z",
            "source": "simulator",
        },
        "S05": {
            "station_id": "S05",
            "name": "Khu Hải Âu phía Đông Nam",
            "latitude": 20.9910,
            "longitude": 105.9560,
            "pm25": 22.0,
            "aqi": 72,
            "co2": 510.0,
            "noise_db": 53.0,
            "temperature": 28.2,
            "status": "online",
            "freshness": "fresh",
            "updated_at": "2026-08-27T14:00:00Z",
            "source": "simulator",
        },
    }


@pytest.fixture
def agent_service():
    return GeospatialAgentService(telemetry_engine=None)


class TestOverviewAndCorrection:
    # -------------------------------------------------------------------------
    # T01: Overview intent & OCP1 scope detection
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "query",
        [
            "Chất lượng không khí chung của Ocean Park 1 thế nào?",
            "Không khí toàn khu hiện thế nào?",
            "Tình hình chung cả khu thế nào?",
            "AQI toàn Ocean Park 1?",
            "Tổng quan chất lượng không khí OCP1?",
            "Chất lượng không khí chung của cả khu?",
            "Tình trạng không khí chung hiện tại?",
            "Cả Ocean Park thì sao?",
        ],
    )
    def test_t01_overview_intent_and_scope(self, agent_service, mock_snapshots, query):
        res = agent_service.process_query(
            message=query,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "environment.overview"
        assert res.get("scope", {}).get("id") == "ocp1"
        assert "overall_aqi" in res
        assert "AQI đại diện toàn khu" in res["response"] or "AQI đại diện" in res["response"]
        assert "VinUni" in res["response"]
        assert "Trục Đa Tốn" in res["response"] or "San Hô" in res["response"] or "S01" in res["response"]

    # -------------------------------------------------------------------------
    # T02: Ranking best location
    # -------------------------------------------------------------------------
    def test_t02_ranking_best_location(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="Khu nào sạch nhất?",
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "recommend_outdoor_location"
        assert "VinUni" in res["response"]
        # Must not be an overview
        assert res["intent"] != "environment.overview"

    # -------------------------------------------------------------------------
    # T03: Ranking worst location
    # -------------------------------------------------------------------------
    def test_t03_ranking_worst_location(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="Khu nào ô nhiễm nhất?",
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "find_worst_location"
        assert res["intent"] != "environment.overview"

    # -------------------------------------------------------------------------
    # T04: Single location inquiry
    # -------------------------------------------------------------------------
    def test_t04_single_location_inquiry(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="Không khí VinUni thế nào?",
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "get_location_environment"
        assert res["resolved_location"]["id"] == "poi_vinuni"
        assert res["intent"] != "environment.overview"

    # -------------------------------------------------------------------------
    # T05: Conversational correction
    # -------------------------------------------------------------------------
    def test_t05_conversational_correction(self, agent_service, mock_snapshots):
        conv_id = "test_conv_t05"
        conversation_state_manager.reset_state(conv_id)

        # Turn 1: User asks a question
        turn1 = agent_service.process_query(
            message="Không khí ở VinUni thế nào?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn1["intent"] == "get_location_environment"

        # Turn 2: User corrects the Agent: "Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1"
        turn2 = agent_service.process_query(
            message="Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn2["intent"] == "environment.overview"
        assert turn2.get("scope", {}).get("id") == "ocp1"
        assert "AQI đại diện toàn khu" in turn2["response"] or "AQI đại diện" in turn2["response"]

        # Verify state in manager has no leftover single location
        state = conversation_state_manager.get_or_create_state(conv_id)
        assert state.active_scope == "ocp1"

    # -------------------------------------------------------------------------
    # T06: Overview map action validation
    # -------------------------------------------------------------------------
    def test_t06_overview_map_actions(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="Chất lượng không khí chung của cả khu Ocean Park 1 thế nào?",
            station_snapshots=mock_snapshots,
        )
        actions = res["map_actions"]

        # Must contain fit_bounds
        fit_action = next((a for a in actions if a.get("type") == "fit_bounds"), None)
        assert fit_action is not None
        bounds = fit_action["bounds"]
        # Bounds must cover the full area from south (VinUni ~20.989) to north (Đa Tốn ~21.000)
        assert bounds[0][0] <= 20.990
        assert bounds[1][0] >= 21.000

        # Must highlight all 5 stations
        sensor_actions = [a for a in actions if a.get("type") == "highlight_sensor"]
        assert len(sensor_actions) == 5
        sensor_ids = {a["sensor_id"] for a in sensor_actions}
        assert sensor_ids == {"S01", "S02", "S03", "S04", "S05"}

        # Must NOT zoom or highlight only VinUni as single point
        point_actions = [a for a in actions if a.get("type") == "highlight_point"]
        assert len(point_actions) == 0

    # -------------------------------------------------------------------------
    # T07: Context override (VinUni -> "toàn khu thì sao?")
    # -------------------------------------------------------------------------
    def test_t07_context_override_to_whole_area(self, agent_service, mock_snapshots):
        conv_id = "test_conv_t07"
        conversation_state_manager.reset_state(conv_id)

        # Turn 1: User asks about VinUni
        turn1 = agent_service.process_query(
            message="VinUni thế nào?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn1["intent"] == "get_location_environment"

        # Turn 2: User pivots to whole area: "toàn khu thì sao?"
        turn2 = agent_service.process_query(
            message="toàn khu thì sao?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn2["intent"] == "environment.overview"
        assert turn2.get("scope", {}).get("id") == "ocp1"

    # -------------------------------------------------------------------------
    # Technical leakage prevention
    # -------------------------------------------------------------------------
    def test_overview_zero_technical_leakage(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="Tổng quan chất lượng không khí toàn Ocean Park 1",
            station_snapshots=mock_snapshots,
        )
        summary = res["answer"]["summary"]
        leaks = ResponseValidator.check_technical_leakage(summary)
        assert leaks == [], f"Found technical leakage in overview response: {leaks}"
