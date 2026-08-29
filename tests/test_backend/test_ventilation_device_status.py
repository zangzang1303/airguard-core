from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import app.main as main_mod  # noqa: E402
from app.dependencies.auth import require_manager  # noqa: E402
from app.services.device_service import DeviceService  # noqa: E402

MANAGER_ID = "00000000-0000-0000-0000-000000000901"


class EffectCursor:
    def execute(self, _query: str, _params: tuple[Any, ...]) -> None:
        return None

    def fetchone(self) -> dict[str, Any]:
        return {
            "baseline_pm25": 88.0,
            "current_pm25": 38.0,
            "baseline_co2": 1100.0,
            "current_co2": 520.0,
            "measured_at": datetime.now(UTC),
        }


def device_row(*, started_at: datetime, duration_minutes: int = 45) -> dict[str, Any]:
    return {
        "device_id": "FILTER-01",
        "device_name": "Simulated outdoor filtration unit",
        "device_type": "air_filter",
        "station_id": "S03",
        "station_name": "Ven Hồ Ngọc Trai",
        "latitude": 20.9953,
        "longitude": 105.95,
        "status": "RUNNING_BOOST",
        "is_simulated": True,
        "last_seen_at": started_at,
        "command_intent_id": "00000000-0000-0000-0000-000000000902",
        "approval_request_id": "00000000-0000-0000-0000-000000000903",
        "command": "ventilation_boost",
        "command_status": "succeeded",
        "duration_minutes": duration_minutes,
        "intensity_percent": 80,
        "command_id": "cmd-device-status-1",
        "acknowledged_at": started_at,
        "ack_status": "succeeded",
        "device_state": "RUNNING_BOOST",
        "reviewed_by": MANAGER_ID,
        "reviewed_at": started_at,
        "review_note": "Approved after evidence review.",
    }


def test_device_status_shapes_countdown_and_measured_effectiveness() -> None:
    now = datetime.now(UTC)
    service = DeviceService(object())  # type: ignore[arg-type]
    result = service._shape_device(device_row(started_at=now - timedelta(minutes=22)), EffectCursor())

    assert result["operating_mode"] == "RUNNING_BOOST"
    assert result["is_active"] is True
    assert 22 * 60 <= result["remaining_seconds"] <= 23 * 60
    assert result["effectiveness"]["pm25_reduction_percent"] == 56.8
    assert result["effectiveness"]["co2_reduction_percent"] == 52.7
    assert result["latest_command"]["approved_by"] == MANAGER_ID


def test_elapsed_timed_command_is_presented_as_standby() -> None:
    service = DeviceService(object())  # type: ignore[arg-type]
    result = service._shape_device(
        device_row(started_at=datetime.now(UTC) - timedelta(minutes=46)),
        EffectCursor(),
    )

    assert result["operating_mode"] == "STANDBY"
    assert result["is_active"] is False
    assert result["remaining_seconds"] == 0


def test_manager_stop_button_creates_pending_proposal_without_dispatch(monkeypatch) -> None:
    async def manager_override() -> dict[str, str]:
        return {"user_id": MANAGER_ID, "role": "manager"}

    class FakeDeviceService:
        def get_status(self, device_id: str) -> dict[str, Any]:
            assert device_id == "FILTER-01"
            return {
                "device_id": device_id,
                "station_id": "S03",
                "operating_mode": "RUNNING_BOOST",
                "started_at": datetime.now(UTC).isoformat(),
                "ends_at": (datetime.now(UTC) + timedelta(minutes=23)).isoformat(),
                "latest_command": {"command_intent_id": "intent-1"},
            }

    class FakeApprovalService:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def create_request(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            return {
                "request_id": "00000000-0000-0000-0000-000000000904",
                "status": "pending",
                "version": 1,
                "station_id": kwargs["station_id"],
                "device_id": kwargs["device_id"],
                "proposed_action": kwargs["proposed_action"],
            }

    approvals = FakeApprovalService()
    monkeypatch.setattr(main_mod, "device_service", FakeDeviceService())
    monkeypatch.setattr(main_mod, "approval_service", approvals)
    monkeypatch.setattr(main_mod, "_enqueue_manager_proposal_notification", lambda **_kwargs: None)
    main_mod.app.dependency_overrides[require_manager] = manager_override
    try:
        client = TestClient(main_mod.app)
        client.cookies.set("airguard_session", "test-session")
        client.cookies.set("airguard_csrf", "csrf-token")
        response = client.post(
            "/api/v1/devices/FILTER-01/proposals",
            headers={"X-CSRF-Token": "csrf-token", "Idempotency-Key": "device-stop-001"},
            json={"action": "standby", "reason": "Operator requests an audited safe stop."},
        )
    finally:
        main_mod.app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert approvals.calls[0]["proposed_action"] == "standby"
    assert "approve" not in approvals.calls[0]
