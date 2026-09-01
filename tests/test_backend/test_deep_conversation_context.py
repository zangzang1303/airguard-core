"""Dedicated Test Suite for Deep Conversation Context & Multi-turn Follow-up Agent.

Tests the stateful 4-layer context resolution, pending action management,
slot filling, task modification, anaphoric references, and seamless Chat/Map synchronization.
"""

from __future__ import annotations

from typing import Any

import pytest

from backend.app.services.conversation_state_manager import conversation_state_manager
from backend.app.services.geospatial_agent_service import geospatial_agent


def _mock_grounded_snapshots(polluted: bool = True) -> dict[str, dict[str, Any]]:
    pm = 85.0 if polluted else 22.0
    aqi_val = 165 if polluted else 45
    now_iso = "2026-08-27T20:00:00Z"
    return {
        "S01": {
            "station_id": "S01",
            "name": "Khu Sapphire 1",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "pm25": pm,
            "aqi": aqi_val,
            "co2": 520,
            "noise_db": 55,
            "temperature": 29.5,
            "timestamp": now_iso,
            "updated_at": now_iso,
            "status": "online",
            "freshness": "fresh",
            "source": "simulator",
        },
        "S02": {
            "station_id": "S02",
            "name": "Phân khu Ruby & The Zenpark",
            "latitude": 20.9940,
            "longitude": 105.9380,
            "pm25": pm - 5,
            "aqi": aqi_val - 10,
            "co2": 510,
            "noise_db": 53,
            "temperature": 29.2,
            "timestamp": now_iso,
            "updated_at": now_iso,
            "status": "online",
            "freshness": "fresh",
            "source": "simulator",
        },
        "S03": {
            "station_id": "S03",
            "name": "Công viên ven hồ San Hô",
            "latitude": 20.9935,
            "longitude": 105.9405,
            "pm25": pm - 8,
            "aqi": aqi_val - 15,
            "co2": 480,
            "noise_db": 48,
            "temperature": 28.5,
            "timestamp": now_iso,
            "updated_at": now_iso,
            "status": "online",
            "freshness": "fresh",
            "source": "simulator",
        },
        "S04": {
            "station_id": "S04",
            "name": "Đại học VinUni",
            "latitude": 20.9898,
            "longitude": 105.9467,
            "pm25": pm - 15,
            "aqi": aqi_val - 25,
            "co2": 460,
            "noise_db": 45,
            "temperature": 28.0,
            "timestamp": now_iso,
            "updated_at": now_iso,
            "status": "online",
            "freshness": "fresh",
            "source": "simulator",
        },
        "S05": {
            "station_id": "S05",
            "name": "Khu Biệt thự Ngọc Trai",
            "latitude": 20.9953,
            "longitude": 105.9500,
            "pm25": pm - 12,
            "aqi": aqi_val - 20,
            "co2": 470,
            "noise_db": 46,
            "temperature": 28.2,
            "timestamp": now_iso,
            "updated_at": now_iso,
            "status": "online",
            "freshness": "fresh",
            "source": "simulator",
        },
    }


class TestDeepConversationContext:
    def setup_method(self) -> None:
        conversation_state_manager._sessions.clear()

    # -------------------------------------------------------------------------
    # T01: Accept Pending Offer ("tìm cho tôi")
    # -------------------------------------------------------------------------
    def test_accept_pending_offer_find_indoor(self) -> None:
        conv_id = "test_t01_accept"
        snapshots = _mock_grounded_snapshots(polluted=True)

        # Turn 1: User asks to run near Sapphire when air is polluted
        res1 = geospatial_agent.process_query(
            message="Tôi muốn chạy bộ ở Sapphire",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "indoor" in res1["intent"].lower() or "trong nhà" in res1["response"].lower() or "CẢNH BÁO" in res1["response"]

        # Check pending action was registered
        state = conversation_state_manager.get_or_create_state(conv_id)
        assert state.dialogue.get("pending_action") is not None

        # Turn 2: User responds with short confirmation "tìm cho tôi"
        res2 = geospatial_agent.process_query(
            message="tìm cho tôi",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert res2["intent"] == "recommend_indoor_activity"
        assert "Vincom" in res2["response"] or "Gym" in res2["response"] or "Club House" in res2["response"]
        assert len(res2["map_actions"]) > 0

    # -------------------------------------------------------------------------
    # T02: Short Yes Confirmations ("được", "ok", "làm đi")
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("yes_phrase", ["được", "ok", "làm đi", "chạy luôn", "đồng ý", "ừ"])
    def test_short_yes_confirmation(self, yes_phrase: str) -> None:
        conv_id = f"test_t02_{yes_phrase}"
        snapshots = _mock_grounded_snapshots(polluted=True)

        # Pre-set pending action
        conversation_state_manager.set_pending_action(
            conv_id,
            action_type="find_nearby_indoor_places",
            known_slots={"origin": "Khu Sapphire"},
        )

        res = geospatial_agent.process_query(
            message=yes_phrase,
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert res["intent"] == "recommend_indoor_activity"
        assert len(res["map_actions"]) > 0

    # -------------------------------------------------------------------------
    # T03: Reject Pending Offer ("thôi", "không cần", "cancel")
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("no_phrase", ["thôi", "không cần", "khỏi", "bỏ đi", "cancel"])
    def test_reject_pending_offer(self, no_phrase: str) -> None:
        conv_id = f"test_t03_{no_phrase}"
        snapshots = _mock_grounded_snapshots(polluted=True)

        conversation_state_manager.set_pending_action(
            conv_id,
            action_type="find_nearby_indoor_places",
            known_slots={"origin": "Khu Sapphire"},
        )

        res = geospatial_agent.process_query(
            message=no_phrase,
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert res["intent"] == "conversation.reject" or "social" in res.get("intent", "")
        assert "hủy" in res["response"].lower() or "không có gì" in res["response"].lower() or "nếu cần" in res["response"].lower()

        # Verify state is cleared
        state = conversation_state_manager.get_or_create_state(conv_id)
        assert state.dialogue.get("pending_action") is None

    # -------------------------------------------------------------------------
    # T04: Numeric Slot Filling ("Bạn muốn chạy bao nhiêu km?" -> "3")
    # -------------------------------------------------------------------------
    def test_numeric_slot_filling_distance(self) -> None:
        conv_id = "test_t04_slot_dist"
        snapshots = _mock_grounded_snapshots(polluted=False)

        conversation_state_manager.update_state(
            conv_id,
            intent="recommend_running_route",
            user_goal="chạy bộ",
        )
        conversation_state_manager.set_awaiting_slot(
            conv_id,
            slot_name="distance_km",
            for_intent="recommend_running_route",
            options=["2", "3", "5"],
        )

        res = geospatial_agent.process_query(
            message="3",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "intent" in res
        assert "3" in res["response"] or "km" in res["response"].lower()

    # -------------------------------------------------------------------------
    # T05: Ordinal Slot Filling ("cái giữa", "cái đầu", "cái cuối")
    # -------------------------------------------------------------------------
    def test_ordinal_slot_filling(self) -> None:
        conv_id = "test_t05_ordinal"
        snapshots = _mock_grounded_snapshots(polluted=False)

        conversation_state_manager.update_state(
            conv_id,
            intent="recommend_running_route",
        )
        conversation_state_manager.set_awaiting_slot(
            conv_id,
            slot_name="distance_km",
            for_intent="recommend_running_route",
            options=["2.0", "3.0", "5.0"],
        )

        res = geospatial_agent.process_query(
            message="cái giữa",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "km" in res["response"].lower() or "chạy" in res["response"].lower()

    # -------------------------------------------------------------------------
    # T06: Modify Route Distance ("ngắn hơn chút", "3 km thôi")
    # -------------------------------------------------------------------------
    def test_modify_distance_shorter(self) -> None:
        conv_id = "test_t06_shorter"
        snapshots = _mock_grounded_snapshots(polluted=False)

        # Turn 1: 5km route
        res1 = geospatial_agent.process_query(
            message="Tìm đường chạy 5km từ Sapphire",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "5" in res1["response"]

        # Turn 2: "3 km thôi"
        res2 = geospatial_agent.process_query(
            message="3 km thôi",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "3" in res2["response"] or "km" in res2["response"].lower()

    # -------------------------------------------------------------------------
    # T07: Route Avoidance Constraint ("nhưng tránh Đa Tốn nhé")
    # -------------------------------------------------------------------------
    def test_modify_avoidance_constraint(self) -> None:
        conv_id = "test_t07_avoid"
        snapshots = _mock_grounded_snapshots(polluted=False)

        # Turn 1: running route
        geospatial_agent.process_query(
            message="Gợi ý cung đường chạy từ Sapphire",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )

        # Turn 2: Avoidance follow-up
        res2 = geospatial_agent.process_query(
            message="nhưng tránh Đa Tốn nhé",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "tránh" in res2["response"].lower() or "đa tốn" in res2["response"].lower()

    # -------------------------------------------------------------------------
    # T08: Anaphora Single Focus ("ở đó chất lượng thế nào")
    # -------------------------------------------------------------------------
    def test_anaphora_single_location(self) -> None:
        conv_id = "test_t08_anaphora"
        snapshots = _mock_grounded_snapshots(polluted=False)

        # Turn 1: Focus VinUni
        res1 = geospatial_agent.process_query(
            message="Chất lượng không khí ở VinUni thế nào?",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "VinUni" in res1["response"]

        # Turn 2: "ở đó có ô nhiễm không?"
        res2 = geospatial_agent.process_query(
            message="ở đó có ô nhiễm không?",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "VinUni" in res2["response"] or "AQI" in res2["response"]

    # -------------------------------------------------------------------------
    # T09: Ambiguous Reference Clarification (2 candidates from comparison)
    # -------------------------------------------------------------------------
    def test_anaphora_ambiguous_two_candidates(self) -> None:
        conv_id = "test_t09_ambig"
        snapshots = _mock_grounded_snapshots(polluted=False)

        # Turn 1: Compare VinUni and Hồ Ngọc Trai
        res1 = geospatial_agent.process_query(
            message="So sánh VinUni và Hồ Ngọc Trai",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "VinUni" in res1["response"] and "Hồ Ngọc Trai" in res1["response"]

        # Turn 2: Ambiguous reference "đi bộ tới đó mất bao lâu?"
        res2 = geospatial_agent.process_query(
            message="đi tới đó mất bao lâu?",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert res2["intent"] in {"conversation.clarification", "clarification"}
        assert "VinUni" in res2["response"] or "Hồ Ngọc Trai" in res2["response"]

    # -------------------------------------------------------------------------
    # T10: Elliptical Follow-up ("còn Sapphire?")
    # -------------------------------------------------------------------------
    def test_elliptical_followup(self) -> None:
        conv_id = "test_t10_elliptical"
        snapshots = _mock_grounded_snapshots(polluted=False)

        # Turn 1: VinUni
        geospatial_agent.process_query(
            message="Chất lượng không khí ở VinUni thế nào?",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )

        # Turn 2: "còn Sapphire?"
        res2 = geospatial_agent.process_query(
            message="còn Sapphire?",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "Sapphire" in res2["response"]
        assert "AQI" in res2["response"]

    # -------------------------------------------------------------------------
    # T11: DoD Multi-turn Cycling Flow
    # -------------------------------------------------------------------------
    def test_cycling_multiturn_dod_flow(self) -> None:
        conv_id = "test_t11_dod_flow"
        snapshots = _mock_grounded_snapshots(polluted=True)

        # Turn 1: "tôi có thể đạp xe thay vì chạy bộ ko"
        res1 = geospatial_agent.process_query(
            message="tôi có thể đạp xe thay vì chạy bộ ko",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "đạp xe" in res1["response"].lower() or "trong nhà" in res1["response"].lower()

        # Turn 2: "trong nhà" -> Agent prompts for activity subtype (gym / walking)
        res2 = geospatial_agent.process_query(
            message="trong nhà",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "Gym" in res2["response"] or "phòng" in res2["response"].lower() or "trong nhà" in res2["response"].lower()

        # Turn 3: "gym" -> Agent executes indoor gym search near Sapphire
        res3 = geospatial_agent.process_query(
            message="gym",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert res3["intent"] == "recommend_indoor_activity"
        assert "Sapphire" in res3["response"] or "Zenpark" in res3["response"] or "Club House" in res3["response"]
        assert len(res3["map_actions"]) > 0

    # -------------------------------------------------------------------------
    # T12: Social Interruption & Context Resumption
    # -------------------------------------------------------------------------
    def test_social_interruption_and_context_resumption(self) -> None:
        conv_id = "test_t12_social"
        snapshots = _mock_grounded_snapshots(polluted=False)

        # Turn 1: Domain query
        res1 = geospatial_agent.process_query(
            message="Chất lượng không khí ở Sapphire thế nào?",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "Sapphire" in res1["response"]

        # Turn 2: Social interruption "bạn bao tuổi"
        res2 = geospatial_agent.process_query(
            message="bạn bao tuổi",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        assert "trợ lý AI" in res2["response"] or "tuổi" in res2["response"]

        # Turn 3: Contextual resumption "ở đó có chạy bộ được không?"
        res3 = geospatial_agent.process_query(
            message="ở đó có chạy bộ được không?",
            conversation_id=conv_id,
            station_snapshots=snapshots,
        )
        # Should remember Sapphire from Turn 1!
        assert "Sapphire" in res3["response"] or "AQI" in res3["response"]
