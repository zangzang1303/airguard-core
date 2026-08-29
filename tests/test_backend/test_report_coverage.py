from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.report_coverage_service import build_coverage_analytics, window_coverage
from app.services.report_policy import ReportPolicy


def _row(at: datetime, value: float = 20, station_id: str = "S01") -> dict:
    return {
        "station_id": station_id,
        "measured_at": at,
        "pm25": value,
        "quality_flag": "valid",
    }


def test_window_coverage_uses_half_open_range_and_exact_boundary() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    policy = ReportPolicy(expected_sample_interval_seconds=15, minimum_coverage_ratio=0.75)
    rows = [_row(start + timedelta(seconds=value)) for value in (0, 15, 30)]
    rows.append(_row(start + timedelta(seconds=60), 999))

    result = window_coverage(
        rows,
        station_id="S01",
        start=start,
        end=start + timedelta(seconds=60),
        policy=policy,
    )

    assert result["valid_sample_count"] == 3
    assert result["expected_sample_count"] == 4
    assert result["coverage_ratio"] == 0.75
    assert result["eligible"] is True
    assert result["value"] == 20


def test_window_coverage_rejects_just_below_threshold_and_non_finite() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    policy = ReportPolicy(expected_sample_interval_seconds=10, minimum_coverage_ratio=0.75)
    rows = [_row(start + timedelta(seconds=index * 10)) for index in range(74)]
    rows.extend([_row(start + timedelta(seconds=740), float("nan")), _row(start, float("inf"))])
    result = window_coverage(
        rows,
        station_id="S01",
        start=start,
        end=start + timedelta(seconds=1000),
        policy=policy,
    )
    assert result["coverage_ratio"] == 0.74
    assert result["eligible"] is False


def test_dst_missing_and_repeated_hours_use_elapsed_utc_duration() -> None:
    zone = ZoneInfo("America/New_York")
    policy = ReportPolicy(expected_sample_interval_seconds=3600)

    spring = build_coverage_analytics(
        [],
        period_start=datetime(2026, 3, 8, 0, tzinfo=zone).astimezone(UTC),
        period_end=datetime(2026, 3, 15, 0, tzinfo=zone).astimezone(UTC),
        timezone_name="America/New_York",
        report_type="weekly",
        active_station_ids=["S01"],
        policy=policy,
    )
    spring_cells = spring["weekly_matrix"]["views"][1]["cells"]
    missing = next(cell for cell in spring_cells if cell["local_date"] == "2026-03-08" and cell["local_hour"] == 2)
    assert missing["expected_sample_count"] == 0
    assert missing["status"] == "not_applicable"

    fall = build_coverage_analytics(
        [],
        period_start=datetime(2026, 11, 1, 0, tzinfo=zone).astimezone(UTC),
        period_end=datetime(2026, 11, 8, 0, tzinfo=zone).astimezone(UTC),
        timezone_name="America/New_York",
        report_type="weekly",
        active_station_ids=["S01"],
        policy=policy,
    )
    fall_cells = fall["weekly_matrix"]["views"][1]["cells"]
    repeated = next(cell for cell in fall_cells if cell["local_date"] == "2026-11-01" and cell["local_hour"] == 1)
    assert repeated["expected_sample_count"] == 2

