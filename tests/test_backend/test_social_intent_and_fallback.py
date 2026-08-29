"""Dedicated Test Suite for Social Intent, Domain Boundary Detection & Fallback Routing.

Tests requirements from docs/AirGuard_Task_Fix_Social_Intent_Domain_Fallback.md:
- T01: "bạn bao tuổi" -> social.assistant_identity, map_actions = 0, tool_calls = 0
- T02: "bạn bao nhiêu tuổi" -> social.assistant_identity, no AQI/VinUni hallucination
- T03: Multi-turn isolation (Turn 1: VinUni -> Turn 2: "bạn bao tuổi" -> social response without VinUni)
- T04: Multi-turn resumption (Turn 1: VinUni -> Turn 2: "bạn bao tuổi" -> Turn 3: "còn AQI ở đó?" -> resumes VinUni)
- T05: "bạn khỏe không" -> social.smalltalk
- T06: "bạn làm được gì" -> conversation.capability
- T07: Unknown query "abcxyz" -> conversation.unknown, clarification prompt without VinUni fallback
"""

import pytest
from backend.app.services.conversation_state_manager import conversation_state_manager
from backend.app.services.conversational_agent_service import conversational_agent
from backend.app.services.geospatial_agent_service import GeospatialAgentService


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


class TestSocialIntentAndFallback:
    # -------------------------------------------------------------------------
    # T01: "bạn bao tuổi"
    # -------------------------------------------------------------------------
    def test_t01_assistant_age_query(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="bạn bao tuổi",
            station_snapshots=mock_snapshots,
            map_context={"selected_location": "poi_vinuni"},
        )
        assert res["intent"] == "social.assistant_identity"
        assert res["map_actions"] == []
        assert res["evidence"] == []
        assert "không có tuổi" in res["response"] or "AI" in res["response"]
        assert "AQI" not in res["response"]
        assert "Hồ Ngọc Trai" not in res["response"]
        assert "VinUni" not in res["response"]

    # -------------------------------------------------------------------------
    # T02: "bạn bao nhiêu tuổi"
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "query",
        [
            "bạn bao nhiêu tuổi",
            "bạn mấy tuổi",
            "bao nhiêu tuổi rồi",
            "tuổi của bạn là bao nhiêu",
        ],
    )
    def test_t02_assistant_age_variations(self, agent_service, mock_snapshots, query):
        res = agent_service.process_query(
            message=query,
            station_snapshots=mock_snapshots,
            map_context={"selected_sensor": "S04", "selected_location": "poi_vinuni"},
        )
        assert res["intent"] == "social.assistant_identity"
        assert res["map_actions"] == []
        assert "không có tuổi" in res["response"] or "AI" in res["response"]
        assert "VinUni" not in res["response"]

    # -------------------------------------------------------------------------
    # T03: Multi-turn isolation (Turn 1: VinUni -> Turn 2: "bạn bao tuổi")
    # -------------------------------------------------------------------------
    def test_t03_multi_turn_isolation(self, agent_service, mock_snapshots):
        conv_id = "test_conv_t03"
        conversation_state_manager.reset_state(conv_id)

        # Turn 1: User asks for cleanest location
        turn1 = agent_service.process_query(
            message="Khu nào sạch nhất?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn1["intent"] == "recommend_outdoor_location"
        assert "VinUni" in turn1["response"]
        assert len(turn1["map_actions"]) > 0

        # Turn 2: User asks "bạn bao tuổi"
        turn2 = agent_service.process_query(
            message="bạn bao tuổi",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn2["intent"] == "social.assistant_identity"
        assert turn2["map_actions"] == []
        assert "không có tuổi" in turn2["response"]
        # Must NOT inherit previous turn's recommendation or location
        assert "VinUni" not in turn2["response"]

    # -------------------------------------------------------------------------
    # T04: Multi-turn domain context resumption
    # -------------------------------------------------------------------------
    def test_t04_multi_turn_resumption(self, agent_service, mock_snapshots):
        conv_id = "test_conv_t04"
        conversation_state_manager.reset_state(conv_id)

        # Turn 1: Cleanest location
        turn1 = agent_service.process_query(
            message="Khu nào sạch nhất?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert "VinUni" in turn1["response"]

        # Turn 2: Social age query
        turn2 = agent_service.process_query(
            message="bạn bao nhiêu tuổi",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn2["intent"] == "social.assistant_identity"

        # Turn 3: User resumes domain query about VinUni
        turn3 = agent_service.process_query(
            message="AQI ở VinUni thì sao?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn3["intent"] == "get_location_environment"
        assert "VinUni" in turn3["response"]
        assert len(turn3["map_actions"]) > 0

    # -------------------------------------------------------------------------
    # T05: Smalltalk ("bạn khỏe không", "cảm ơn", "tạm biệt")
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "query,expected_kind",
        [
            ("bạn khỏe không", "wellbeing"),
            ("cảm ơn nhé", "acknowledgement"),
            ("tạm biệt bạn", "farewell"),
        ],
    )
    def test_t05_smalltalk_queries(self, agent_service, mock_snapshots, query, expected_kind):
        res = agent_service.process_query(
            message=query,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "social.smalltalk"
        assert res["map_actions"] == []
        assert res["evidence"] == []

    # -------------------------------------------------------------------------
    # T06: Capability inquiry ("bạn làm được gì")
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "query",
        [
            "bạn làm được gì",
            "bạn có thể giúp gì cho tôi",
            "tôi có thể hỏi gì",
            "bạn giúp được gì ở đây",
        ],
    )
    def test_t06_capability_inquiries(self, agent_service, mock_snapshots, query):
        res = agent_service.process_query(
            message=query,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "conversation.capability"
        assert res["map_actions"] == []
        assert "chất lượng không khí" in res["response"]
        assert "dự báo" in res["response"] or "so sánh" in res["response"]

    # -------------------------------------------------------------------------
    # T07: Unknown query ("abcxyz", "cái này thế nào") -> Fallback clarification
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "query",
        [
            "abcxyz",
            "cái này thế nào",
            "được không nhỉ",
        ],
    )
    def test_t07_unknown_query_fallback(self, agent_service, mock_snapshots, query):
        res = agent_service.process_query(
            message=query,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "conversation.unknown"
        assert res["map_actions"] == []
        assert res["evidence"] == []
        # Must prompt for clarification, NOT return VinUni or Hồ Ngọc Trai
        assert "VinUni" not in res["response"]
        assert "Hồ Ngọc Trai" not in res["response"]
        assert "Bạn muốn mình kiểm tra" in res["response"] or "chất lượng không khí" in res["response"]
