from __future__ import annotations

import json
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
            "action": "notify_station_area_users",
            "approval_id": "approval-1",
            "idempotency_key": "approval:approval-1:v2",
            "timestamp": "2026-08-08T10:00:00+00:00",
        }
    )

    assert command.approval_id == "approval-1"
    assert command.idempotency_key.endswith(":v2")


def test_device_command_rejects_missing_approval_reference() -> None:
    payload = {
        "command_id": "cmd-1",
        "device_id": "FILTER-01",
        "action": "notify_station_area_users",
        "idempotency_key": "key-1",
        "timestamp": "2026-08-08T10:00:00+00:00",
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
        "action": "notify_station_area_users",
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
