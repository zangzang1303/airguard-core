from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.core import Settings  # noqa: E402
from app.schemas.measurements import MeasurementIngestionRequest  # noqa: E402
from app.services.alert_engine import AlertEngine  # noqa: E402
from app.services.approval_service import ApprovalService  # noqa: E402
from app.services.database import ServiceError  # noqa: E402
from app.services.ingestion_service import MeasurementIngestionService  # noqa: E402
from app.services.station_service import pm25_level  # noqa: E402
from app.services.air_quality import aqi_category, pm25_aqi  # noqa: E402
from app.services.forecast_service import InsufficientForecastHistory, trend_forecast  # noqa: E402
from app.services.weather_service import WeatherService  # noqa: E402


def test_settings_load_thresholds_from_environment() -> None:
    os.environ["PM25_WARNING_THRESHOLD"] = "55"
    os.environ["PM25_CRITICAL_THRESHOLD"] = "120"
    settings = Settings.load()

    assert settings.alert_warning_threshold == 55
    assert settings.alert_critical_threshold == 120


def test_settings_load_alert_consecutive_measurements() -> None:
    previous = os.environ.get("PM25_ALERT_CONSECUTIVE_MEASUREMENTS")
    try:
        os.environ["PM25_ALERT_CONSECUTIVE_MEASUREMENTS"] = "3"
        settings = Settings.load()
        assert settings.alert_consecutive_measurements == 3
    finally:
        if previous is None:
            os.environ.pop("PM25_ALERT_CONSECUTIVE_MEASUREMENTS", None)
        else:
            os.environ["PM25_ALERT_CONSECUTIVE_MEASUREMENTS"] = previous


def test_settings_reject_invalid_alert_consecutive_measurements() -> None:
    previous = os.environ.get("PM25_ALERT_CONSECUTIVE_MEASUREMENTS")
    try:
        os.environ["PM25_ALERT_CONSECUTIVE_MEASUREMENTS"] = "0"
        try:
            Settings.load()
        except ValueError as exc:
            assert "CONSECUTIVE" in str(exc)
        else:
            raise AssertionError("zero consecutive measurements should be rejected")
    finally:
        if previous is None:
            os.environ.pop("PM25_ALERT_CONSECUTIVE_MEASUREMENTS", None)
        else:
            os.environ["PM25_ALERT_CONSECUTIVE_MEASUREMENTS"] = previous


def test_pm25_level_boundaries() -> None:
    assert pm25_level(None) is None
    assert pm25_level(25) == "good"
    assert pm25_level(50) == "moderate"
    assert pm25_level(100) == "unhealthy"
    assert pm25_level(101) == "very_unhealthy"


def test_pm25_aqi_breakpoints() -> None:
    assert pm25_aqi(None) is None
    assert pm25_aqi(12.0) == 50
    assert pm25_aqi(12.1) == 51
    assert pm25_aqi(35.4) == 100
    assert pm25_aqi(35.5) == 101
    assert aqi_category(151) == "unhealthy"


def test_short_term_forecast_uses_history_trend_not_current_value_repeat() -> None:
    start = datetime(2026, 8, 13, 10, tzinfo=UTC)
    result = trend_forecast(
        [
            {"measured_at": start, "pm25": 20},
            {"measured_at": start + timedelta(minutes=10), "pm25": 25},
            {"measured_at": start + timedelta(minutes=20), "pm25": 30},
            {"measured_at": start + timedelta(minutes=30), "pm25": 35},
        ],
        3,
        generated_at=start + timedelta(minutes=30),
    )

    assert result["model_name"] == "damped_linear_trend_v1"
    assert result["items"][0]["pm25"] > 35
    assert result["items"][2]["pm25"] > result["items"][0]["pm25"]
    assert result["items"][0]["pm25_min"] < result["items"][0]["pm25_max"]
    assert result["items"][0]["forecast_at"].endswith("+00:00")


def test_short_term_forecast_refuses_to_repeat_current_for_insufficient_history() -> None:
    start = datetime(2026, 8, 13, 10, tzinfo=UTC)
    try:
        trend_forecast([{"measured_at": start, "pm25": 20}], 1)
    except InsufficientForecastHistory:
        pass
    else:
        raise AssertionError("forecast should require enough history to estimate a trend")


def test_manager_guard_rejects_non_manager() -> None:
    try:
        ApprovalService._require_manager("viewer")
    except ServiceError as exc:
        assert exc.status_code == 403
        assert exc.code == "forbidden"
    else:
        raise AssertionError("viewer role should not pass manager guard")


def test_weather_has_explicit_freshness() -> None:
    weather = WeatherService().current_weather()

    assert weather["is_stale"] is False
    assert weather["source"] == "simulator_fallback_weather"
    assert weather["is_fallback"] is True
    assert weather["observed_at"]


def test_alert_source_is_derived_from_rule_version() -> None:
    alert = AlertEngine._with_source({"rule_version": "pm25-threshold-v1"})

    assert alert["source"] == "backend_alert_rule:pm25-threshold-v1"


def test_alert_threshold_requires_consecutive_fresh_values() -> None:
    engine = AlertEngine(
        db=object(),
        station_service=object(),
        audit=object(),
        warning_threshold=50,
        critical_threshold=100,
        rule_version="test-rule",
        consecutive_measurements=2,
    )

    assert engine._threshold_is_qualified([60]) is False
    assert engine._threshold_is_qualified([60, 65]) is True
    assert engine._threshold_is_qualified([60, 45]) is False


def test_environmental_alert_rules_and_recommendations_are_deterministic() -> None:
    engine = AlertEngine(
        db=object(), station_service=object(), audit=object(),
        warning_threshold=50, critical_threshold=100, rule_version="pm25-test",
    )
    co2_rule = next(rule for rule in engine.rules if rule.alert_type == "co2_threshold")
    aqi_rule = next(rule for rule in engine.rules if rule.alert_type == "aqi_threshold")

    assert engine._severity_for(999, co2_rule) is None
    assert engine._severity_for(1000, co2_rule) == "warning"
    assert engine._severity_for(151, aqi_rule) == "critical"
    assert "thông gió" in engine._recommendation(co2_rule, "warning")


def test_stale_ingestion_is_rejected_before_database_write() -> None:
    class NoWriteDatabase:
        def connection(self):
            raise AssertionError("stale measurements must not reach persistence")

    service = MeasurementIngestionService(NoWriteDatabase(), stale_after_seconds=120)
    request = MeasurementIngestionRequest(
        message_id="MSG-stale",
        station_id="S01",
        pm25=90,
        timestamp=datetime.now(UTC) - timedelta(minutes=10),
        source="simulator",
    )

    try:
        service.ingest(request)
    except ServiceError as exc:
        assert exc.code == "stale"
        assert exc.status_code == 422
    else:
        raise AssertionError("stale measurement should be rejected")



def test_user_id_validation_accepts_uuid() -> None:
    assert ApprovalService._validate_user_id("00000000-0000-0000-0000-000000000001") == "00000000-0000-0000-0000-000000000001"


def test_user_id_validation_rejects_plain_text() -> None:
    try:
        ApprovalService._validate_user_id("demo-manager")
    except ServiceError as exc:
        assert exc.status_code == 422
        assert exc.code == "invalid_user_id"
    else:
        raise AssertionError("plain text user id should not pass UUID validation")


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
            print(f"PASS {name}")
