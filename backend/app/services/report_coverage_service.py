from __future__ import annotations

import math
from datetime import UTC, date, datetime, time, timedelta, timezone
from statistics import fmean
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .report_policy import (
    GOOD_HOUR_PM25_THRESHOLD,
    MATRIX_COLOR_SCALE_VERSION,
    MATRIX_COLOR_STOPS,
    ReportPolicy,
)


def build_coverage_analytics(
    measurements: list[dict[str, Any]],
    *,
    period_start: datetime,
    period_end: datetime,
    timezone_name: str,
    report_type: str,
    active_station_ids: list[str],
    policy: ReportPolicy,
) -> dict[str, Any]:
    zone = _load_zone(timezone_name)
    station_ids = sorted({str(value) for value in active_station_ids if str(value).strip()})
    normalized = _valid_pm25_rows(measurements)
    local_dates = _local_dates(period_start, period_end, zone)
    station_hours: dict[str, list[dict[str, Any]]] = {}
    station_days: list[dict[str, Any]] = []

    for station_id in station_ids:
        rows = [row for row in normalized if row["station_id"] == station_id]
        hours = [
            _hour_cell(
                rows,
                station_id=station_id,
                local_day=local_day,
                local_hour=hour,
                zone=zone,
                policy=policy,
            )
            for local_day in local_dates
            for hour in range(24)
        ]
        station_hours[station_id] = hours
        for local_day in local_dates:
            station_days.append(
                _station_day(
                    station_id,
                    local_day,
                    rows,
                    [cell for cell in hours if cell["local_date"] == local_day.isoformat()],
                    zone,
                    policy,
                )
            )

    matrix = _weekly_matrix(
        report_type,
        local_dates,
        station_ids,
        station_hours,
        policy,
    )
    return {
        "reference_comparison": {
            "station_days": station_days,
            "annual_compliance_evaluated": False,
        },
        "weekly_matrix": matrix,
        "active_station_ids": station_ids,
    }


def window_coverage(
    measurements: list[dict[str, Any]],
    *,
    station_id: str,
    start: datetime,
    end: datetime,
    policy: ReportPolicy,
) -> dict[str, Any]:
    expected = _expected_count(start, end, policy.expected_sample_interval_seconds)
    values = [
        row["pm25"]
        for row in _valid_pm25_rows(measurements)
        if row["station_id"] == station_id and start <= row["measured_at"] < end
    ]
    raw_coverage = len(values) / expected if expected > 0 else 0.0
    return {
        "value": fmean(values) if values else None,
        "valid_sample_count": len(values),
        "expected_sample_count": expected,
        "coverage_ratio": _ratio(raw_coverage),
        "eligible": expected > 0 and raw_coverage >= policy.minimum_coverage_ratio,
    }


def _station_day(
    station_id: str,
    local_day: date,
    rows: list[dict[str, Any]],
    hour_cells: list[dict[str, Any]],
    zone: timezone | ZoneInfo,
    policy: ReportPolicy,
) -> dict[str, Any]:
    start_local = datetime.combine(local_day, time.min, tzinfo=zone)
    end_local = datetime.combine(local_day + timedelta(days=1), time.min, tzinfo=zone)
    start = start_local.astimezone(UTC)
    end = end_local.astimezone(UTC)
    day_values = [row["pm25"] for row in rows if start <= row["measured_at"] < end]
    expected = _expected_count(start, end, policy.expected_sample_interval_seconds)
    raw_coverage = len(day_values) / expected if expected else 0.0
    applicable = [cell for cell in hour_cells if cell["status"] != "not_applicable"]
    eligible = [cell for cell in applicable if cell["status"] == "eligible"]
    day_eligible = (
        expected > 0
        and raw_coverage >= policy.minimum_coverage_ratio
        and len(eligible) == len(applicable)
    )
    average = fmean(day_values) if day_values and day_eligible else None
    good_count = sum(
        1 for cell in eligible if cell["value"] is not None and cell["value"] <= GOOD_HOUR_PM25_THRESHOLD
    )
    good_rate = good_count / len(eligible) if eligible else None
    status = "eligible" if day_eligible else "insufficient_data"
    qcvn_status = "not_comparable" if day_eligible else "insufficient_data"
    who_status = "insufficient_data"
    if day_eligible and average is not None:
        who_status = "below_reference" if average <= 15 else "above_reference"
    return {
        "station_id": station_id,
        "local_date": local_day.isoformat(),
        "avg_pm25_ug_m3": round(average, 2) if average is not None else None,
        "valid_sample_count": len(day_values),
        "expected_sample_count": expected,
        "coverage_ratio": _ratio(raw_coverage),
        "eligible_hour_count": len(eligible),
        "applicable_hour_count": len(applicable),
        "status": status,
        "qcvn": {
            "reference_name": "QCVN 05:2023/BTNMT",
            "threshold": 45,
            "unit": "ug/Nm3",
            "effective_from": "2026-01-01",
            "status": qcvn_status,
            "relation": None,
            "not_legally_comparable": True,
            "annual_compliance_evaluated": False,
        },
        "who": {
            "reference_name": "WHO 2021 PM2.5 24-hour guideline",
            "threshold": 15,
            "unit": "ug/m3",
            "status": who_status,
            "is_legal_standard": False,
            "annual_compliance_evaluated": False,
        },
        "good_hour_kpi": {
            "policy_version": policy.good_hour_policy_version,
            "good_hour_count": good_count,
            "eligible_hour_count": len(eligible),
            "good_hour_rate": round(good_rate, 4) if good_rate is not None else None,
            "target_ratio": policy.good_hour_target_ratio,
            "target_met": good_rate >= policy.good_hour_target_ratio if good_rate is not None else None,
            "status": "available" if good_rate is not None else "insufficient_data",
            "is_compliance_metric": False,
        },
    }


def _weekly_matrix(
    report_type: str,
    local_dates: list[date],
    station_ids: list[str],
    station_hours: dict[str, list[dict[str, Any]]],
    policy: ReportPolicy,
) -> dict[str, Any]:
    base = {
        "metric": "pm25",
        "unit": "ug/m3",
        "station_options": ["all_stations", *station_ids],
        "color_scale": {
            "version": MATRIX_COLOR_SCALE_VERSION,
            "clamp": True,
            "stops": [int(value) if value.is_integer() else value for value in MATRIX_COLOR_STOPS],
            "palette": ["#e8f5e9", "#b9e4c9", "#f4e38b", "#f6b26b", "#e06666", "#8e3b63"],
        },
    }
    if report_type != "weekly":
        return {**base, "status": "not_applicable", "views": []}

    dates = local_dates[:7]
    while len(dates) < 7 and dates:
        dates.append(dates[-1] + timedelta(days=1))
    if not dates:
        return {**base, "status": "available", "views": []}

    views: list[dict[str, Any]] = []
    expected_keys = [(day.isoformat(), hour) for day in dates for hour in range(24)]
    for station_id in station_ids:
        indexed = {
            (cell["local_date"], cell["local_hour"]): cell
            for cell in station_hours.get(station_id, [])
        }
        cells = [indexed.get(key) or _missing_cell(*key, len(station_ids)) for key in expected_keys]
        views.append({"station_selector": station_id, "cells": cells})

    all_cells: list[dict[str, Any]] = []
    for local_date, local_hour in expected_keys:
        candidates = [
            cell
            for station_id in station_ids
            for cell in station_hours.get(station_id, [])
            if cell["local_date"] == local_date
            and cell["local_hour"] == local_hour
            and cell["status"] == "eligible"
        ]
        applicable = any(
            cell["status"] != "not_applicable"
            for station_id in station_ids
            for cell in station_hours.get(station_id, [])
            if cell["local_date"] == local_date and cell["local_hour"] == local_hour
        )
        station_ratio = len(candidates) / len(station_ids) if station_ids else 0.0
        eligible = (
            applicable
            and len(candidates) >= policy.matrix_min_eligible_stations
            and station_ratio >= policy.minimum_coverage_ratio
        )
        all_cells.append(
            {
                "local_date": local_date,
                "local_hour": local_hour,
                "value": round(fmean(cell["value"] for cell in candidates), 2) if eligible else None,
                "valid_sample_count": sum(cell["valid_sample_count"] for cell in candidates),
                "expected_sample_count": sum(cell["expected_sample_count"] for cell in candidates),
                "coverage_ratio": _ratio(station_ratio),
                "eligible_station_count": len(candidates),
                "active_station_count": len(station_ids),
                "status": "eligible" if eligible else ("insufficient_data" if applicable else "not_applicable"),
            }
        )
    views.insert(0, {"station_selector": "all_stations", "cells": all_cells})
    return {**base, "status": "available", "views": views}


def _hour_cell(
    rows: list[dict[str, Any]],
    *,
    station_id: str,
    local_day: date,
    local_hour: int,
    zone: timezone | ZoneInfo,
    policy: ReportPolicy,
) -> dict[str, Any]:
    start_local = datetime.combine(local_day, time(local_hour), tzinfo=zone)
    next_wall = datetime.combine(
        local_day + timedelta(days=1) if local_hour == 23 else local_day,
        time(0 if local_hour == 23 else local_hour + 1),
        tzinfo=zone,
    )
    start = start_local.astimezone(UTC)
    end = next_wall.astimezone(UTC)
    expected = _expected_count(start, end, policy.expected_sample_interval_seconds)
    values = [row["pm25"] for row in rows if start <= row["measured_at"] < end]
    raw_coverage = len(values) / expected if expected else 0.0
    applicable = expected > 0
    eligible = applicable and raw_coverage >= policy.minimum_coverage_ratio
    return {
        "local_date": local_day.isoformat(),
        "local_hour": local_hour,
        "value": round(fmean(values), 2) if values and eligible else None,
        "valid_sample_count": len(values),
        "expected_sample_count": expected,
        "coverage_ratio": _ratio(raw_coverage),
        "eligible_station_count": 1 if eligible else 0,
        "active_station_count": 1,
        "status": "eligible" if eligible else ("insufficient_data" if applicable else "not_applicable"),
        "station_id": station_id,
    }


def _missing_cell(local_date: str, local_hour: int, active_count: int) -> dict[str, Any]:
    return {
        "local_date": local_date,
        "local_hour": local_hour,
        "value": None,
        "valid_sample_count": 0,
        "expected_sample_count": 0,
        "coverage_ratio": 0.0,
        "eligible_station_count": 0,
        "active_station_count": active_count,
        "status": "insufficient_data",
    }


def _valid_pm25_rows(measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    for raw in measurements:
        if str(raw.get("quality_flag", "valid")).lower() != "valid":
            continue
        measured_at = _aware(raw.get("measured_at"))
        pm25 = _finite(raw.get("pm25"))
        station_id = str(raw.get("station_id") or "").strip()
        if measured_at is None or pm25 is None or pm25 < 0 or not station_id:
            continue
        accepted.append({"station_id": station_id, "measured_at": measured_at, "pm25": pm25})
    return accepted


def _local_dates(
    period_start: datetime,
    period_end: datetime,
    zone: timezone | ZoneInfo,
) -> list[date]:
    start_day = period_start.astimezone(zone).date()
    last_moment = period_end.astimezone(UTC) - timedelta(microseconds=1)
    end_day = last_moment.astimezone(zone).date()
    count = max(0, (end_day - start_day).days + 1)
    return [start_day + timedelta(days=index) for index in range(count)]


def _expected_count(start: datetime, end: datetime, cadence: int) -> int:
    elapsed = max(0.0, (end.astimezone(UTC) - start.astimezone(UTC)).total_seconds())
    return int(round(elapsed / cadence))


def _ratio(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


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


def _load_zone(name: str) -> timezone | ZoneInfo:
    if name in {"UTC", "Etc/UTC", "GMT"}:
        return UTC
    if name == "Asia/Ho_Chi_Minh":
        return timezone(timedelta(hours=7), name=name)
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError("invalid IANA timezone") from exc
