from datetime import UTC, datetime, timedelta

from app.services.report_coverage_service import build_coverage_analytics
from app.services.report_policy import ReportPolicy


def _weekly_rows(station_values: dict[str, float]) -> list[dict]:
    start = datetime(2026, 8, 17, tzinfo=UTC)
    return [
        {
            "station_id": station_id,
            "measured_at": start + timedelta(hours=hour, minutes=5),
            "pm25": value,
            "quality_flag": "valid",
        }
        for station_id, value in station_values.items()
        for hour in range(168)
    ]


def test_weekly_matrix_has_168_cells_and_unweighted_all_station_mean() -> None:
    station_values = {"S01": 10.0, "S02": 20.0, "S03": 30.0, "S04": 40.0}
    result = build_coverage_analytics(
        _weekly_rows(station_values),
        period_start=datetime(2026, 8, 17, tzinfo=UTC),
        period_end=datetime(2026, 8, 24, tzinfo=UTC),
        timezone_name="UTC",
        report_type="weekly",
        active_station_ids=list(station_values),
        policy=ReportPolicy(expected_sample_interval_seconds=3600),
    )
    matrix = result["weekly_matrix"]
    assert matrix["color_scale"]["version"] == "pm25-fixed-scale-v1"
    assert matrix["color_scale"]["stops"] == [0, 15, 35, 45, 75, 150]
    assert all(len(view["cells"]) == 168 for view in matrix["views"])
    all_cells = matrix["views"][0]["cells"]
    assert all(cell["status"] == "eligible" for cell in all_cells)
    assert all(cell["value"] == 25 for cell in all_cells)
    assert all(cell["eligible_station_count"] == 4 for cell in all_cells)


def test_all_stations_gate_returns_null_instead_of_good_color() -> None:
    result = build_coverage_analytics(
        _weekly_rows({"S01": 5.0, "S02": 6.0}),
        period_start=datetime(2026, 8, 17, tzinfo=UTC),
        period_end=datetime(2026, 8, 24, tzinfo=UTC),
        timezone_name="UTC",
        report_type="weekly",
        active_station_ids=["S01", "S02", "S03", "S04", "S05"],
        policy=ReportPolicy(expected_sample_interval_seconds=3600, matrix_min_eligible_stations=3),
    )
    cells = result["weekly_matrix"]["views"][0]["cells"]
    assert all(cell["status"] == "insufficient_data" for cell in cells)
    assert all(cell["value"] is None for cell in cells)


def test_daily_report_does_not_invent_weekly_matrix() -> None:
    result = build_coverage_analytics(
        [],
        period_start=datetime(2026, 8, 17, tzinfo=UTC),
        period_end=datetime(2026, 8, 18, tzinfo=UTC),
        timezone_name="UTC",
        report_type="daily",
        active_station_ids=["S01"],
        policy=ReportPolicy(),
    )
    assert result["weekly_matrix"]["status"] == "not_applicable"
    assert result["weekly_matrix"]["views"] == []

