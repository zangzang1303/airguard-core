from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from .report_coverage_service import window_coverage
from .report_policy import ENERGY_BASELINE_VERSION, ReportPolicy

ESG_REASON_CODES = {
    "no_acknowledged_boost_cycles",
    "no_acknowledged_eco_intervals",
    "missing_device_profile",
    "ambiguous_device_profile",
    "invalid_device_profile",
    "uncorrelated_ack",
    "out_of_order_ack",
    "missing_duration",
    "interval_too_short",
    "station_unavailable",
    "insufficient_before_coverage",
    "insufficient_after_coverage",
}


def calculate_esg_metrics(
    *,
    command_intents: list[dict[str, Any]],
    device_status_events: list[dict[str, Any]],
    device_profiles: list[dict[str, Any]],
    measurements: list[dict[str, Any]],
    period_start: datetime,
    period_end: datetime,
    policy: ReportPolicy,
) -> dict[str, Any]:
    intervals, rejected = build_acknowledged_mode_intervals(
        command_intents,
        device_status_events,
        period_start=period_start,
        period_end=period_end,
    )
    pm25 = _estimated_pm25_removed(
        intervals,
        device_profiles,
        measurements,
        policy,
    )
    energy = _estimated_energy_saved(intervals, device_profiles, policy)
    if rejected:
        pm25["excluded_inputs"] = rejected
        energy["excluded_inputs"] = rejected
    return {
        "estimated_pm25_removed_kg": pm25,
        "estimated_energy_saved_kwh": energy,
        "acknowledged_intervals": [_public_interval(item) for item in intervals],
    }


def build_acknowledged_mode_intervals(
    command_intents: list[dict[str, Any]],
    device_status_events: list[dict[str, Any]],
    *,
    period_start: datetime,
    period_end: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    intents = {str(row.get("command_intent_id")): row for row in command_intents if row.get("command_intent_id")}
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for event in device_status_events:
        if str(event.get("status") or "").lower() != "succeeded":
            continue
        intent_id = str(event.get("command_intent_id") or "")
        intent = intents.get(intent_id)
        if intent is None:
            rejected.append({"event_id": str(event.get("event_id") or ""), "reason_code": "uncorrelated_ack"})
            continue
        if str(event.get("device_id") or "") != str(intent.get("device_id") or ""):
            rejected.append({"command_intent_id": intent_id, "reason_code": "uncorrelated_ack"})
            continue
        command_id = str(event.get("command_id") or "")
        if not command_id or command_id != str(intent.get("command_id") or ""):
            rejected.append({"command_intent_id": intent_id, "reason_code": "uncorrelated_ack"})
            continue
        created_at = _aware(intent.get("created_at"))
        dispatched_at = _aware(intent.get("dispatched_at"))
        observed_at = _aware(event.get("observed_at"))
        if (
            created_at is None
            or dispatched_at is None
            or observed_at is None
            or not (observed_at >= dispatched_at >= created_at)
        ):
            rejected.append({"command_intent_id": intent_id, "reason_code": "out_of_order_ack"})
            continue
        duration = _positive_number(intent.get("duration_minutes"))
        if duration is None:
            rejected.append({"command_intent_id": intent_id, "reason_code": "missing_duration"})
            continue
        station_id = str(intent.get("station_id") or "")
        if not station_id:
            rejected.append({"command_intent_id": intent_id, "reason_code": "station_unavailable"})
            continue
        candidates.append(
            {
                "command_intent_id": intent_id,
                "command_id": command_id,
                "device_id": str(intent["device_id"]),
                "station_id": station_id,
                "mode": str(intent.get("command") or "").lower(),
                "acknowledged_at": observed_at,
                "duration_minutes": duration,
                "is_simulated": bool(event.get("is_simulated", True)),
            }
        )

    candidates.sort(key=lambda row: (row["device_id"], row["acknowledged_at"], row["command_intent_id"]))
    by_device: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_device[row["device_id"]].append(row)
    intervals: list[dict[str, Any]] = []
    for rows in by_device.values():
        for index, row in enumerate(rows):
            start = row["acknowledged_at"]
            next_start = rows[index + 1]["acknowledged_at"] if index + 1 < len(rows) else period_end
            intended_end = start + timedelta(minutes=row["duration_minutes"])
            end = min(intended_end, next_start, period_end)
            clipped_start = max(start, period_start)
            if end <= clipped_start:
                continue
            intervals.append(
                {
                    **row,
                    "start": clipped_start,
                    "end": end,
                    "acknowledged_mode_hours": (end - clipped_start).total_seconds() / 3600,
                }
            )
    intervals.sort(key=lambda row: (row["start"], row["device_id"], row["command_intent_id"]))
    return intervals, rejected


def _estimated_energy_saved(
    intervals: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    policy: ReportPolicy,
) -> dict[str, Any]:
    eco = [row for row in intervals if row["mode"] == "eco_mode"]
    if not eco:
        return _insufficient("no_acknowledged_eco_intervals", policy, "eligible_interval_count")
    total = 0.0
    inputs: list[dict[str, Any]] = []
    for interval in eco:
        profile, reason = _profile_for_interval(interval, profiles)
        if reason:
            return _insufficient(reason, policy, "eligible_interval_count")
        assert profile is not None
        boost_kw = _positive_number(profile.get("boost_power_kw"))
        eco_kw = _positive_number(profile.get("eco_power_kw"), allow_zero=True)
        if boost_kw is None or eco_kw is None or boost_kw < eco_kw:
            return _insufficient("invalid_device_profile", policy, "eligible_interval_count")
        value = (boost_kw - eco_kw) * interval["acknowledged_mode_hours"]
        total += value
        inputs.append(
            {
                "command_intent_id": interval["command_intent_id"],
                "device_id": interval["device_id"],
                "profile_id": str(profile.get("profile_id")),
                "profile_version": str(profile.get("profile_version")),
                "interval_start": interval["start"].isoformat(),
                "interval_end": interval["end"].isoformat(),
                "acknowledged_mode_hours": interval["acknowledged_mode_hours"],
                "boost_power_kw": boost_kw,
                "eco_power_kw": eco_kw,
                "is_simulated": bool(profile.get("is_simulated")),
                "calibration_source": str(profile.get("calibration_source")),
            }
        )
    return {
        "value": round(total, 6),
        "status": "complete",
        "reason_code": None,
        "formula_version": policy.esg_formula_version,
        "baseline_version": ENERGY_BASELINE_VERSION,
        "unit": "kWh",
        "eligible_interval_count": len(inputs),
        "inputs": inputs,
        "is_counterfactual_estimate": True,
        "is_metered_energy": False,
    }


def _estimated_pm25_removed(
    intervals: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    measurements: list[dict[str, Any]],
    policy: ReportPolicy,
) -> dict[str, Any]:
    boosts = [row for row in intervals if row["mode"] == "ventilation_boost"]
    if not boosts:
        return _insufficient("no_acknowledged_boost_cycles", policy, "eligible_cycle_count")
    total = 0.0
    inputs: list[dict[str, Any]] = []
    last_reason = "interval_too_short"
    for interval in boosts:
        if interval["acknowledged_mode_hours"] < 0.25:
            last_reason = "interval_too_short"
            continue
        profile, reason = _profile_for_interval(interval, profiles)
        if reason:
            return _insufficient(reason, policy, "eligible_cycle_count")
        assert profile is not None
        airflow = _positive_number(profile.get("airflow_m3_per_hour"))
        if airflow is None:
            return _insufficient("invalid_device_profile", policy, "eligible_cycle_count")
        before_start = interval["acknowledged_at"] - timedelta(minutes=15)
        before_end = interval["acknowledged_at"]
        after_start = interval["end"] - timedelta(minutes=15)
        after_end = interval["end"]
        before = window_coverage(
            measurements,
            station_id=interval["station_id"],
            start=before_start,
            end=before_end,
            policy=policy,
        )
        after = window_coverage(
            measurements,
            station_id=interval["station_id"],
            start=after_start,
            end=after_end,
            policy=policy,
        )
        if not before["eligible"]:
            last_reason = "insufficient_before_coverage"
            continue
        if not after["eligible"]:
            last_reason = "insufficient_after_coverage"
            continue
        delta = max(float(before["value"]) - float(after["value"]), 0.0)
        volume = airflow * interval["acknowledged_mode_hours"]
        total += delta * volume * 1e-9
        inputs.append(
            {
                "command_intent_id": interval["command_intent_id"],
                "device_id": interval["device_id"],
                "station_id": interval["station_id"],
                "profile_id": str(profile.get("profile_id")),
                "profile_version": str(profile.get("profile_version")),
                "before_window_start": before_start.isoformat(),
                "before_window_end": before_end.isoformat(),
                "after_window_start": after_start.isoformat(),
                "after_window_end": after_end.isoformat(),
                "before_avg_pm25_ug_m3": before["value"],
                "after_avg_pm25_ug_m3": after["value"],
                "delta_pm25_ug_m3": delta,
                "airflow_m3_per_hour": airflow,
                "airflow_volume_m3": volume,
                "acknowledged_mode_hours": interval["acknowledged_mode_hours"],
                "is_simulated": bool(profile.get("is_simulated")),
                "calibration_source": str(profile.get("calibration_source")),
            }
        )
    if not inputs:
        return _insufficient(last_reason, policy, "eligible_cycle_count")
    return {
        "value": round(total, 9),
        "status": "complete",
        "reason_code": None,
        "formula_version": policy.esg_formula_version,
        "unit": "kg",
        "eligible_cycle_count": len(inputs),
        "inputs": inputs,
        "is_before_after_estimate": True,
        "causal_effect_established": False,
    }


def _profile_for_interval(
    interval: dict[str, Any], profiles: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, str | None]:
    matches = []
    for profile in profiles:
        if str(profile.get("device_id") or "") != interval["device_id"]:
            continue
        effective_from = _aware(profile.get("effective_from"))
        effective_to = _aware(profile.get("effective_to"))
        if effective_from is None:
            continue
        if effective_from <= interval["start"] and (effective_to is None or interval["end"] <= effective_to):
            matches.append(profile)
    if not matches:
        return None, "missing_device_profile"
    if len(matches) > 1:
        return None, "ambiguous_device_profile"
    return matches[0], None


def _insufficient(reason: str, policy: ReportPolicy, count_key: str) -> dict[str, Any]:
    return {
        "value": None,
        "status": "insufficient_data",
        "reason_code": reason if reason in ESG_REASON_CODES else "invalid_device_profile",
        "formula_version": policy.esg_formula_version,
        "unit": "kg" if count_key == "eligible_cycle_count" else "kWh",
        count_key: 0,
        "inputs": [],
    }


def _public_interval(interval: dict[str, Any]) -> dict[str, Any]:
    return {
        "command_intent_id": interval["command_intent_id"],
        "command_id": interval["command_id"],
        "device_id": interval["device_id"],
        "station_id": interval["station_id"],
        "mode": interval["mode"],
        "start": interval["start"].isoformat(),
        "end": interval["end"].isoformat(),
        "acknowledged_mode_hours": round(interval["acknowledged_mode_hours"], 6),
        "is_simulated": interval["is_simulated"],
    }


def _aware(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        candidate = value
    elif isinstance(value, str):
        try:
            candidate = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if candidate.tzinfo is None or candidate.utcoffset() is None:
        return None
    return candidate.astimezone(UTC)


def _positive_number(value: Any, *, allow_zero: bool = False) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        return None
    return number
