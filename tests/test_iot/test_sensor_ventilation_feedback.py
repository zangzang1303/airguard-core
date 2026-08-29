from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

SIMULATOR_PATH = Path(__file__).resolve().parents[2] / "services" / "sensor-simulator"
sys.path.insert(0, str(SIMULATOR_PATH))

import sensor_simulator as simulator  # noqa: E402


def test_approved_boost_status_drives_exponential_pm25_and_co2_decay() -> None:
    started_at = datetime(2026, 8, 29, 8, tzinfo=UTC)
    simulator.active_ventilation.clear()
    simulator.handle_device_status(
        {
            "command_id": "cmd-feedback-1",
            "device_id": "FILTER-01",
            "station_id": "S03",
            "status": "succeeded",
            "device_state": "RUNNING_BOOST",
            "started_at": started_at.isoformat(),
            "ends_at": (started_at + timedelta(minutes=45)).isoformat(),
            "duration_minutes": 45,
            "intensity_percent": 80,
        }
    )

    initial = simulator.apply_ventilation_feedback("S03", 88.0, 1100.0, started_at)
    after_fifteen = simulator.apply_ventilation_feedback(
        "S03", 88.0, 1100.0, started_at + timedelta(minutes=15)
    )

    assert initial == (88.0, 1100.0)
    assert after_fifteen[0] < 40
    assert after_fifteen[1] < 720


def test_eco_or_expired_cycle_stops_applying_boost_decay() -> None:
    now = datetime(2026, 8, 29, 8, tzinfo=UTC)
    simulator.active_ventilation.clear()
    simulator.handle_device_status(
        {
            "command_id": "cmd-feedback-2",
            "device_id": "FILTER-01",
            "station_id": "S03",
            "status": "succeeded",
            "device_state": "RUNNING_BOOST",
            "started_at": (now - timedelta(minutes=46)).isoformat(),
            "ends_at": (now - timedelta(minutes=1)).isoformat(),
            "duration_minutes": 45,
            "intensity_percent": 80,
        }
    )

    assert simulator.apply_ventilation_feedback("S03", 80.0, 1000.0, now) == (80.0, 1000.0)
    assert "S03" not in simulator.active_ventilation
