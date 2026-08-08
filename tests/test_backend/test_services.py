from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.core import Settings  # noqa: E402
from app.services.alert_engine import AlertEngine  # noqa: E402
from app.services.approval_service import ApprovalService  # noqa: E402
from app.services.database import ServiceError  # noqa: E402
from app.services.station_service import pm25_level  # noqa: E402
from app.services.weather_service import WeatherService  # noqa: E402


def test_settings_load_thresholds_from_environment() -> None:
    os.environ["PM25_WARNING_THRESHOLD"] = "55"
    os.environ["PM25_CRITICAL_THRESHOLD"] = "120"
    settings = Settings.load()

    assert settings.alert_warning_threshold == 55
    assert settings.alert_critical_threshold == 120


def test_pm25_level_boundaries() -> None:
    assert pm25_level(None) is None
    assert pm25_level(25) == "good"
    assert pm25_level(50) == "moderate"
    assert pm25_level(100) == "unhealthy"
    assert pm25_level(101) == "very_unhealthy"


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


def test_alert_source_is_derived_from_rule_version() -> None:
    alert = AlertEngine._with_source({"rule_version": "pm25-threshold-v1"})

    assert alert["source"] == "backend_alert_rule:pm25-threshold-v1"



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
