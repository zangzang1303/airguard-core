from datetime import UTC, datetime, timedelta

from app.services.report_esg_service import build_acknowledged_mode_intervals, calculate_esg_metrics
from app.services.report_policy import ReportPolicy

START = datetime(2026, 8, 17, tzinfo=UTC)


def _intent(intent_id: str, command_id: str, command: str, ack_hour: float, duration: int) -> dict:
    return {
        "command_intent_id": intent_id,
        "command_id": command_id,
        "device_id": "FILTER-01",
        "station_id": "S03",
        "command": command,
        "duration_minutes": duration,
        "created_at": START + timedelta(hours=ack_hour - 0.2),
        "dispatched_at": START + timedelta(hours=ack_hour - 0.1),
    }


def _event(intent_id: str, command_id: str, ack_hour: float) -> dict:
    return {
        "event_id": intent_id,
        "command_intent_id": intent_id,
        "command_id": command_id,
        "device_id": "FILTER-01",
        "status": "succeeded",
        "observed_at": START + timedelta(hours=ack_hour),
        "is_simulated": True,
    }


def _profile() -> dict:
    return {
        "profile_id": "profile-1",
        "device_id": "FILTER-01",
        "profile_version": "sim-v1",
        "effective_from": START - timedelta(days=1),
        "effective_to": None,
        "airflow_m3_per_hour": 1000,
        "boost_power_kw": 3,
        "eco_power_kw": 1,
        "calibration_source": "simulator_fixture_not_field_calibration",
        "is_simulated": True,
    }


def _measurements(equal: bool = False) -> list[dict]:
    rows = []
    for minute in (45, 50, 55):
        rows.append({"station_id": "S03", "measured_at": START + timedelta(minutes=minute), "pm25": 30, "quality_flag": "valid"})
    for minute in (75, 80, 85):
        rows.append({"station_id": "S03", "measured_at": START + timedelta(minutes=minute), "pm25": 30 if equal else 20, "quality_flag": "valid"})
    return rows


def test_esg_complete_fixture_and_complete_zero_are_distinct_from_missing() -> None:
    intents = [
        _intent("boost", "cmd-boost", "ventilation_boost", 1, 30),
        _intent("eco", "cmd-eco", "eco_mode", 2, 30),
    ]
    events = [_event("boost", "cmd-boost", 1), _event("eco", "cmd-eco", 2)]
    policy = ReportPolicy(expected_sample_interval_seconds=300)
    result = calculate_esg_metrics(
        command_intents=intents,
        device_status_events=events,
        device_profiles=[_profile()],
        measurements=_measurements(),
        period_start=START,
        period_end=START + timedelta(hours=3),
        policy=policy,
    )
    assert result["estimated_pm25_removed_kg"]["value"] == 0.000005
    assert result["estimated_pm25_removed_kg"]["status"] == "complete"
    assert result["estimated_energy_saved_kwh"]["value"] == 1.0
    assert result["estimated_energy_saved_kwh"]["baseline_version"] == "boost_baseline_v1"

    zero = calculate_esg_metrics(
        command_intents=intents,
        device_status_events=events,
        device_profiles=[_profile()],
        measurements=_measurements(equal=True),
        period_start=START,
        period_end=START + timedelta(hours=3),
        policy=policy,
    )
    assert zero["estimated_pm25_removed_kg"]["value"] == 0
    assert zero["estimated_pm25_removed_kg"]["status"] == "complete"

    missing = calculate_esg_metrics(
        command_intents=intents,
        device_status_events=events,
        device_profiles=[],
        measurements=_measurements(),
        period_start=START,
        period_end=START + timedelta(hours=3),
        policy=policy,
    )
    assert missing["estimated_pm25_removed_kg"]["value"] is None
    assert missing["estimated_pm25_removed_kg"]["reason_code"] == "missing_device_profile"


def test_acknowledged_intervals_are_clipped_by_next_successful_ack() -> None:
    intents = [
        _intent("one", "cmd-one", "ventilation_boost", 1, 60),
        _intent("two", "cmd-two", "eco_mode", 1.5, 60),
    ]
    intervals, rejected = build_acknowledged_mode_intervals(
        intents,
        [_event("one", "cmd-one", 1), _event("two", "cmd-two", 1.5)],
        period_start=START,
        period_end=START + timedelta(hours=3),
    )
    assert rejected == []
    assert intervals[0]["end"] == intervals[1]["start"]
    assert intervals[0]["acknowledged_mode_hours"] == 0.5


def test_uncorrelated_and_out_of_order_ack_never_create_interval() -> None:
    intent = _intent("one", "cmd-one", "eco_mode", 1, 30)
    bad = _event("wrong", "cmd-one", 1)
    intervals, rejected = build_acknowledged_mode_intervals(
        [intent], [bad], period_start=START, period_end=START + timedelta(hours=2)
    )
    assert intervals == []
    assert rejected[0]["reason_code"] == "uncorrelated_ack"

