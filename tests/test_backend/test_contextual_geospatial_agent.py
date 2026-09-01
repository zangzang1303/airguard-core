"""Comprehensive Test Suite for Contextual Geospatial Agent in Vinhomes Ocean Park 1.

Covers all test groups defined in docs/AirGuard_Contextual_Geospatial_Agent_Master_Task.md:
- Group A: Location & Entity Resolver (aliases, accents, abbreviations, road segments)
- Group B: Multi-turn Follow-up Context (worst area -> "Còn VinUni?", comparison chain, route adjustments)
- Group C: Negation & Pivot Handling ("ngoài chạy bộ muốn trong nhà", "tránh Đa Tốn")
- Group D: Unknown Location Fail-Closed (no erroneous fallback)
- Group E: Decision Engine (Best time to exercise / run tonight)
- Group F: Technical Leakage Guard (zero internal tokens)
- Group G: Map / Chat Consistency & Evidence Integrity
"""

import pytest

from backend.app.services.conversation_state_manager import conversation_state_manager
from backend.app.services.geospatial_agent_service import GeospatialAgentService
from backend.app.services.response_composer import ResponseValidator
from backend.app.services.spatial_registry import spatial_registry


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


# ==============================================================================
# GROUP A: Location & Entity Resolver
# ==============================================================================
class TestGroupALocationResolver:
    @pytest.mark.parametrize(
        "query,expected_id",
        [
            ("vinuni", "poi_vinuni"),
            ("Vin Uni", "poi_vinuni"),
            ("đại học vinuni", "poi_vinuni"),
            ("trường vinuni", "poi_vinuni"),
            ("Hải Đăng", "road_hai_dang"),
            ("hai dang", "road_hai_dang"),
            ("Hải Đăng 6", "road_hai_dang_6"),
            ("hai dang 6", "road_hai_dang_6"),
            ("Sapphire", "poi_sapphire"),
            ("The Sapphire", "poi_sapphire"),
            ("Hồ Ngọc Trai", "poi_ngoc_trai_lake"),
            ("ho ngoc trai", "poi_ngoc_trai_lake"),
            ("Vincom", "poi_vincom"),
            ("Vinmec", "poi_vinmec"),
            ("Zenpark", "poi_zenpark_ruby"),
            ("An Đào", "poi_an_dao"),
            ("Masteri", "poi_masteri"),
            ("San Hô 16", "road_san_ho_16"),
            ("Sao Biển 24", "road_sao_bien_24"),
        ],
    )
    def test_poi_and_road_resolution(self, query, expected_id):
        poi = spatial_registry.find_poi_by_name(query)
        assert poi is not None, f"Failed to resolve '{query}'"
        assert poi["id"] == expected_id


# ==============================================================================
# GROUP B: Multi-turn Follow-up Context
# ==============================================================================
class TestGroupBMultiTurnFollowup:
    def test_worst_location_then_elliptical_comparison(self, agent_service, mock_snapshots):
        conv_id = "test_conv_b1"
        conversation_state_manager.reset_state(conv_id)

        # Turn 1: User asks "Khu nào đang ô nhiễm nhất?"
        turn1 = agent_service.process_query(
            message="Khu nào đang ô nhiễm nhất?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn1["intent"] == "find_worst_location"
        assert ("Trục Đa Tốn" in turn1["response"] or "San Hô" in turn1["response"] or "S01" in turn1["response"])

        # Turn 2: User asks "Còn VinUni thì sao?"
        turn2 = agent_service.process_query(
            message="Còn VinUni thì sao?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn2["intent"] == "compare_locations"
        assert "VinUni" in turn2["response"]

    def test_route_distance_adjustment_followup(self, agent_service, mock_snapshots):
        conv_id = "test_conv_b2"
        conversation_state_manager.reset_state(conv_id)

        # Turn 1: User asks "Tìm cho tôi đường chạy 5 km từ Sapphire"
        turn1 = agent_service.process_query(
            message="Tìm cho tôi đường chạy 5 km từ Sapphire",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn1["intent"] in {"recommend_running_route", "recommend_personalized_running_route"}

        # Turn 2: User asks "Ngắn hơn chút"
        turn2 = agent_service.process_query(
            message="Ngắn hơn chút",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn2["intent"] in {"recommend_running_route", "recommend_personalized_running_route"}
        # Distance should be reduced
        best_route = turn2["best_route"]
        assert best_route["distance_km"] <= 4.0

    def test_comparison_chain_followup(self, agent_service, mock_snapshots):
        conv_id = "test_conv_b3"
        conversation_state_manager.reset_state(conv_id)

        # Turn 1: Compare VinUni and Hồ Ngọc Trai
        turn1 = agent_service.process_query(
            message="So sánh VinUni và Hồ Ngọc Trai",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn1["intent"] == "compare_locations"

        # Turn 2: User asks "Còn Sapphire?"
        turn2 = agent_service.process_query(
            message="Còn Sapphire?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert turn2["intent"] == "compare_locations"
        assert "Sapphire" in turn2["response"]


# ==============================================================================
# GROUP C: Negation & Pivot Handling
# ==============================================================================
class TestGroupCNegationAndPivot:
    def test_indoor_pivot_negation(self, agent_service, mock_snapshots):
        conv_id = "test_conv_c1"
        res = agent_service.process_query(
            message="Ngoài chạy bộ tôi muốn hoạt động khác trong nhà",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "recommend_indoor_activity"
        assert "trong nhà" in res["response"].lower()
        # Should not suggest outdoor running polyline
        actions = res.get("map_actions", [])
        assert not any(a.get("type") == "highlight_route" for a in actions)

    def test_avoid_polluted_area_routing(self, agent_service, mock_snapshots):
        conv_id = "test_conv_c2"
        res = agent_service.process_query(
            message="Tìm cho tôi đường chạy nhưng tránh khu Đa Tốn",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "recommend_avoidance_running_route"
        assert "tránh" in res["response"].lower()
        assert "Đa Tốn" in res["response"]


# ==============================================================================
# GROUP D: Unknown Location Fail-Closed
# ==============================================================================
class TestGroupDUnknownLocation:
    @pytest.mark.parametrize(
        "query,candidate_name",
        [
            ("Không khí ở Hồ Gươm thế nào?", "Hồ Gươm"),
            ("Chất lượng ở khu ABCXYZ ra sao?", "ABCXYZ"),
        ],
    )
    def test_unknown_location_does_not_hallucinate(self, agent_service, mock_snapshots, query, candidate_name):
        res = agent_service.process_query(
            message=query,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "unknown_location"
        assert "chưa xác định được" in res["response"]
        # Must not fallback to VinUni
        assert "VinUni" not in res["answer"]["headline"]


# ==============================================================================
# GROUP E: Decision Engine (Best Time)
# ==============================================================================
class TestGroupEDecisionEngine:
    def test_best_time_to_exercise(self, agent_service, mock_snapshots):
        conv_id = "test_conv_e1"
        res = agent_service.process_query(
            message="Tối nay lúc nào chạy tốt nhất ở VinUni?",
            conversation_id=conv_id,
            station_snapshots=mock_snapshots,
        )
        assert res["intent"] == "decision_best_time"
        assert "thời điểm phù hợp nhất" in res["response"].lower()
        assert "VinUni" in res["response"]
        assert len(res["answer"]["highlights"]) >= 3


# ==============================================================================
# GROUP F: Technical Leakage Guard
# ==============================================================================
class TestGroupFTechnicalLeakageGuard:
    @pytest.mark.parametrize(
        "query",
        [
            "Khu nào đang ô nhiễm nhất?",
            "VinUni hiện thế nào?",
            "So sánh Sapphire và VinUni",
            "Tìm đường chạy 3 km",
            "Ngoài chạy bộ có chỗ nào trong nhà không?",
            "Tối nay mấy giờ chạy tốt nhất?",
            "Tìm đường chạy tránh Đa Tốn",
        ],
    )
    def test_zero_leakage_across_all_intents(self, agent_service, mock_snapshots, query):
        res = agent_service.process_query(
            message=query,
            station_snapshots=mock_snapshots,
        )
        summary = res["answer"]["summary"]
        leaks = ResponseValidator.check_technical_leakage(summary)
        assert leaks == [], f"Detected technical leakage: {leaks} in response: {summary}"


# ==============================================================================
# GROUP G: Map / Chat Consistency & Evidence Integrity
# ==============================================================================
class TestGroupGMapChatConsistency:
    def test_map_actions_match_answer_entity(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="Khu nào đang ô nhiễm nhất?",
            station_snapshots=mock_snapshots,
        )
        actions = res["map_actions"]
        # Should highlight worst station S01 or worst area
        assert any(
            (a.get("type") == "highlight_sensor" and a.get("sensor_id") == "S01")
            or (a.get("type") == "highlight_area" and "da_ton" in str(a.get("area_id")))
            for a in actions
        )

    def test_route_coordinates_provided_in_map_actions(self, agent_service, mock_snapshots):
        res = agent_service.process_query(
            message="Tìm đường chạy 3 km từ VinUni",
            station_snapshots=mock_snapshots,
        )
        actions = res["map_actions"]
        route_action = next((a for a in actions if a.get("type") == "highlight_route"), None)
        assert route_action is not None
        assert len(route_action.get("coordinates", [])) >= 3
