from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.core import Settings  # noqa: E402
from app.schemas.measurements import MeasurementIngestionRequest  # noqa: E402
from app.services.air_quality import aqi_category, pm25_aqi  # noqa: E402
from app.services.alert_engine import AlertEngine  # noqa: E402
from app.services.approval_service import ApprovalService  # noqa: E402
from app.services.database import ServiceError  # noqa: E402
from app.services.forecast_service import InsufficientForecastHistory, trend_forecast  # noqa: E402
from app.services.ingestion_service import MeasurementIngestionService  # noqa: E402
from app.services.station_service import pm25_level  # noqa: E402
from app.services.weather_service import WeatherService  # noqa: E402


def test_settings_load_thresholds_from_environment() -> None:
    os.environ["PM25_WARNING_THRESHOLD"] = "55"
    os.environ["PM25_CRITICAL_THRESHOLD"] = "120"
    settings = Settings.load()

    assert settings.alert_warning_threshold == 55
    assert settings.alert_critical_threshold == 120


def test_settings_enable_automatic_agent_proposals_by_default() -> None:
    previous = os.environ.pop("AUTO_PROPOSAL_ENABLED", None)
    try:
        assert Settings.load().auto_proposal_enabled is True
    finally:
        if previous is not None:
            os.environ["AUTO_PROPOSAL_ENABLED"] = previous


def test_settings_use_fifteen_minute_ventilation_trigger_by_default() -> None:
    previous_seconds = os.environ.pop("VENTILATION_TRIGGER_SECONDS", None)
    previous_minutes = os.environ.pop("VENTILATION_TRIGGER_MINUTES", None)
    try:
        assert Settings.load().ventilation_trigger_seconds == 15 * 60
    finally:
        if previous_seconds is not None:
            os.environ["VENTILATION_TRIGGER_SECONDS"] = previous_seconds
        if previous_minutes is not None:
            os.environ["VENTILATION_TRIGGER_MINUTES"] = previous_minutes


def test_settings_keep_legacy_ventilation_minutes_compatible() -> None:
    previous_seconds = os.environ.pop("VENTILATION_TRIGGER_SECONDS", None)
    previous_minutes = os.environ.get("VENTILATION_TRIGGER_MINUTES")
    try:
        os.environ["VENTILATION_TRIGGER_MINUTES"] = "2"
        assert Settings.load().ventilation_trigger_seconds == 120
    finally:
        if previous_seconds is not None:
            os.environ["VENTILATION_TRIGGER_SECONDS"] = previous_seconds
        if previous_minutes is None:
            os.environ.pop("VENTILATION_TRIGGER_MINUTES", None)
        else:
            os.environ["VENTILATION_TRIGGER_MINUTES"] = previous_minutes


def test_settings_allow_production_frontend_origin_by_default() -> None:
    previous = os.environ.pop("CORS_ORIGINS", None)
    try:
        assert "https://airguard-app.vercel.app" in Settings.load().cors_origins
    finally:
        if previous is not None:
            os.environ["CORS_ORIGINS"] = previous


def test_settings_loads_one_hour_pending_proposal_ttl_by_default() -> None:
    previous = os.environ.pop("PROPOSAL_PENDING_TTL_SECONDS", None)
    try:
        assert Settings.load().proposal_pending_ttl_seconds == 3600
    finally:
        if previous is not None:
            os.environ["PROPOSAL_PENDING_TTL_SECONDS"] = previous


def test_settings_rejects_non_positive_pending_proposal_ttl() -> None:
    previous = os.environ.get("PROPOSAL_PENDING_TTL_SECONDS")
    try:
        os.environ["PROPOSAL_PENDING_TTL_SECONDS"] = "0"
        try:
            Settings.load()
        except ValueError as exc:
            assert "PROPOSAL_PENDING_TTL_SECONDS" in str(exc)
        else:
            raise AssertionError("non-positive proposal TTL should be rejected")
    finally:
        if previous is None:
            os.environ.pop("PROPOSAL_PENDING_TTL_SECONDS", None)
        else:
            os.environ["PROPOSAL_PENDING_TTL_SECONDS"] = previous


def test_settings_loads_global_alert_consecutive_measurements() -> None:
    previous = os.environ.get("ALERT_CONSECUTIVE_MEASUREMENTS")
    try:
        os.environ["ALERT_CONSECUTIVE_MEASUREMENTS"] = "2"
        assert Settings.load().alert_consecutive_measurements == 2
    finally:
        if previous is None:
            os.environ.pop("ALERT_CONSECUTIVE_MEASUREMENTS", None)
        else:
            os.environ["ALERT_CONSECUTIVE_MEASUREMENTS"] = previous


def test_settings_parses_auto_proposal_station_allowlist() -> None:
    previous = os.environ.get("AUTO_PROPOSAL_STATIONS")
    try:
        os.environ["AUTO_PROPOSAL_STATIONS"] = "s05, S05"
        assert Settings.load().auto_proposal_stations == ("S05", "S05")
    finally:
        if previous is None:
            os.environ.pop("AUTO_PROPOSAL_STATIONS", None)
        else:
            os.environ["AUTO_PROPOSAL_STATIONS"] = previous


def test_settings_load_alert_consecutive_measurements() -> None:
    previous = os.environ.get("PM25_ALERT_CONSECUTIVE_MEASUREMENTS")
    previous_global = os.environ.pop("ALERT_CONSECUTIVE_MEASUREMENTS", None)
    try:
        os.environ["PM25_ALERT_CONSECUTIVE_MEASUREMENTS"] = "3"
        settings = Settings.load()
        assert settings.alert_consecutive_measurements == 3
    finally:
        if previous is None:
            os.environ.pop("PM25_ALERT_CONSECUTIVE_MEASUREMENTS", None)
        else:
            os.environ["PM25_ALERT_CONSECUTIVE_MEASUREMENTS"] = previous
        if previous_global is not None:
            os.environ["ALERT_CONSECUTIVE_MEASUREMENTS"] = previous_global


def test_settings_reject_invalid_alert_consecutive_measurements() -> None:
    previous = os.environ.get("PM25_ALERT_CONSECUTIVE_MEASUREMENTS")
    previous_global = os.environ.pop("ALERT_CONSECUTIVE_MEASUREMENTS", None)
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
        if previous_global is not None:
            os.environ["ALERT_CONSECUTIVE_MEASUREMENTS"] = previous_global


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


def test_short_term_forecast_preserves_canonical_aqi_metadata() -> None:
    start = datetime(2026, 8, 13, 10, tzinfo=UTC)
    result = trend_forecast(
        [
            {"measured_at": start, "aqi": 80},
            {"measured_at": start + timedelta(minutes=10), "aqi": 85},
            {"measured_at": start + timedelta(minutes=20), "aqi": 90},
        ],
        3,
        metric="aqi",
        generated_at=start + timedelta(minutes=20),
    )

    assert result["metric"] == "aqi"
    assert result["model_version"] == result["model_name"]
    assert result["freshness"] == "fresh"
    assert result["items"][0]["source"] == result["source"]
    assert [item["hour_offset"] for item in result["items"]] == [1, 2, 3]


def test_short_term_forecast_responds_to_latest_spike_without_cache() -> None:
    start = datetime(2026, 8, 13, 10, tzinfo=UTC)
    result = trend_forecast(
        [
            {"measured_at": start, "pm25": 40},
            {"measured_at": start + timedelta(minutes=10), "pm25": 40},
            {"measured_at": start + timedelta(minutes=20), "pm25": 190},
        ],
        1,
        generated_at=start + timedelta(minutes=20),
    )

    assert result["items"][0]["pm25"] > 190
    assert result["source"] == "simulator_history_damped_linear_v1"


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


def test_weather_uses_valid_open_meteo_current_payload() -> None:
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["wind_speed_unit"] == "ms"
        assert request.url.params["timezone"] == "UTC"
        return httpx.Response(
            200,
            json={
                "current": {
                    "time": "2026-08-23T06:00:00Z",
                    "temperature_2m": 30.2,
                    "relative_humidity_2m": 70,
                    "precipitation": 0.1,
                    "wind_speed_10m": 2.8,
                    "wind_direction_10m": 120,
                }
            },
        )

    weather = WeatherService(
        "https://api.open-meteo.com/v1/forecast",
        max_age_seconds=10**9,
        transport=httpx.MockTransport(handler),
    ).current_weather()

    assert weather["source"] == "open_meteo_forecast_api"
    assert weather["is_fallback"] is False
    assert weather["wind_speed_ms"] == 2.8
    assert weather["wind_direction_deg"] == 120


def test_weather_provider_failure_is_labelled_fallback() -> None:
    import httpx

    weather = WeatherService(
        "https://api.open-meteo.com/v1/forecast",
        transport=httpx.MockTransport(lambda _request: httpx.Response(503)),
    ).current_weather()

    assert weather["source"] == "simulator_fallback_weather"
    assert weather["is_fallback"] is True
    assert weather["fallback_reason"] == "provider_unavailable_or_invalid"


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
    assert engine._threshold_is_qualified([1100, 1200], warning_threshold=1000) is True
    assert engine._threshold_is_qualified([1100, 900], warning_threshold=1000) is False


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
