from __future__ import annotations

import sys
from pathlib import Path

DEVICE_PATH = Path(__file__).resolve().parents[2] / "services" / "device-simulator"
sys.path.insert(0, str(DEVICE_PATH))

from device_simulator import DeviceCommand  # noqa: E402


def test_device_command_requires_server_approval_reference() -> None:
    command = DeviceCommand.model_validate(
        {
            "command_id": "cmd-1",
            "device_id": "FILTER-01",
            "station_id": "S03",
            "action": "ventilation_boost",
            "approval_id": "approval-1",
            "idempotency_key": "approval:approval-1:v2",
            "timestamp": "2026-08-08T10:00:00+00:00",
            "duration_minutes": 45,
            "intensity_percent": 80,
        }
    )

    assert command.approval_id == "approval-1"
    assert command.idempotency_key.endswith(":v2")


def test_device_command_rejects_missing_approval_reference() -> None:
    payload = {
        "command_id": "cmd-1",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "action": "ventilation_boost",
        "idempotency_key": "key-1",
        "timestamp": "2026-08-08T10:00:00+00:00",
        "duration_minutes": 45,
        "intensity_percent": 80,
    }

    try:
        DeviceCommand.model_validate(payload)
    except Exception as exc:
        assert "approval_id" in str(exc)
    else:
        raise AssertionError("device command without approval_id must be rejected")


def test_device_command_rejects_naive_timestamp() -> None:
    payload = {
        "command_id": "cmd-1",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "action": "eco_mode",
        "approval_id": "approval-1",
        "idempotency_key": "key-1",
        "timestamp": "2026-08-08T10:00:00",
    }

    try:
        DeviceCommand.model_validate(payload)
    except Exception as exc:
        assert "timezone" in str(exc)
    else:
        raise AssertionError("device command timestamp must include timezone")


def test_timed_device_command_requires_duration_and_intensity() -> None:
    payload = {
        "command_id": "cmd-2",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "action": "ventilation_boost",
        "approval_id": "approval-2",
        "idempotency_key": "approval:approval-2:v2",
        "timestamp": "2026-08-08T10:00:00+00:00",
    }

    try:
        DeviceCommand.model_validate(payload)
    except Exception as exc:
        assert "duration_minutes" in str(exc)
    else:
        raise AssertionError("timed command without duration/intensity must be rejected")


def test_device_command_action_is_allowlisted() -> None:
    payload = {
        "command_id": "cmd-3",
        "device_id": "FILTER-01",
        "station_id": "S03",
        "action": "notify_station_area_users",
        "approval_id": "approval-3",
        "idempotency_key": "approval:approval-3:v2",
        "timestamp": "2026-08-08T10:00:00+00:00",
    }

    try:
        DeviceCommand.model_validate(payload)
    except Exception as exc:
        assert "action" in str(exc)
    else:
        raise AssertionError("non-device action must not reach the simulator")
