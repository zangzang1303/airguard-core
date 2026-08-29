from __future__ import annotations

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    cors_origins: list[str]
    stale_after_seconds: int
    alert_warning_threshold: float
    alert_critical_threshold: float
    alert_rule_version: str
    alert_consecutive_measurements: int
    environmental_alert_rule_version: str
    aqi_warning_threshold: float
    aqi_critical_threshold: float
    co2_warning_threshold: float
    co2_critical_threshold: float
    noise_warning_threshold: float
    noise_critical_threshold: float
    temperature_warning_threshold: float
    temperature_critical_threshold: float
    agent_service_url: str
    agent_service_timeout_seconds: float
    auto_proposal_enabled: bool
    resident_alert_notifications_enabled: bool
    resident_alert_notification_cooldown_seconds: int
    predictive_warning_policy_version: str
    predictive_warning_notifications_enabled: bool
    predictive_warning_evaluation_interval_seconds: int
    predictive_warning_lead_minutes: int
    predictive_warning_lead_tolerance_minutes: int
    predictive_warning_min_confidence: float
    predictive_warning_forecast_max_age_seconds: int
    predictive_warning_clear_evaluations: int
    proposal_pending_ttl_seconds: int
    auto_proposal_stations: tuple[str, ...]
    ventilation_trigger_seconds: int
    ventilation_recovery_minutes: int
    ventilation_safe_pm25_threshold: float
    ventilation_safe_co2_threshold: float
    ventilation_default_duration_minutes: int
    ventilation_intensity_percent: int
    ventilation_max_gap_seconds: int
    report_timezone: str
    report_policy_version: str
    report_expected_sample_interval_seconds: int
    report_minimum_coverage_ratio: float
    report_matrix_min_eligible_stations: int
    report_narrative_endpoint: str | None
    report_narrative_timeout_seconds: float
    report_narrative_service_token: str | None
    session_ttl_seconds: int
    verification_token_ttl_seconds: int
    reset_token_ttl_seconds: int
    cookie_secure: bool
    cookie_samesite: str
    frontend_url: str
    rate_limit_login_max_attempts: int
    rate_limit_lockout_seconds: int
    auth_demo_mode: bool
    google_client_id: str | None
    google_client_secret: str | None
    google_redirect_uri: str | None
    weather_api_base_url: str | None
    weather_timeout_seconds: float
    weather_latitude: float
    weather_longitude: float
    weather_max_age_seconds: int

    @classmethod
    def load(cls) -> Settings:
        raw_origins = os.getenv(
            "CORS_ORIGINS",
            (
                "https://airguard-app.vercel.app,"
                "http://localhost:5173,http://127.0.0.1:5173"
            ),
        )
        stale_after_seconds = int(os.getenv("STALE_AFTER_SECONDS", "300"))
        if stale_after_seconds <= 0:
            raise ValueError("STALE_AFTER_SECONDS must be positive")

        warning = float(os.getenv("PM25_WARNING_THRESHOLD", "50"))
        critical = float(os.getenv("PM25_CRITICAL_THRESHOLD", "100"))
        if warning <= 0 or critical <= warning:
            raise ValueError("PM25 thresholds must satisfy 0 < warning < critical")
        consecutive_raw = os.getenv("ALERT_CONSECUTIVE_MEASUREMENTS", "").strip()
        consecutive = int(consecutive_raw or os.getenv("PM25_ALERT_CONSECUTIVE_MEASUREMENTS", "2"))
        if consecutive < 1 or consecutive > 20:
            raise ValueError("ALERT_CONSECUTIVE_MEASUREMENTS must be between 1 and 20")
        def threshold_pair(prefix: str, warning_default: str, critical_default: str) -> tuple[float, float]:
            metric_warning = float(os.getenv(f"{prefix}_WARNING_THRESHOLD", warning_default))
            metric_critical = float(os.getenv(f"{prefix}_CRITICAL_THRESHOLD", critical_default))
            if metric_warning <= 0 or metric_critical <= metric_warning:
                raise ValueError(f"{prefix} thresholds must satisfy 0 < warning < critical")
            return metric_warning, metric_critical

        aqi_warning, aqi_critical = threshold_pair("AQI", "101", "151")
        co2_warning, co2_critical = threshold_pair("CO2", "1000", "1500")
        noise_warning, noise_critical = threshold_pair("NOISE_DB", "70", "85")
        temperature_warning, temperature_critical = threshold_pair("TEMPERATURE", "35", "39")
        agent_timeout = float(os.getenv("AGENT_SERVICE_TIMEOUT_SECONDS", "8"))
        if agent_timeout <= 0:
            raise ValueError("AGENT_SERVICE_TIMEOUT_SECONDS must be positive")
        auto_proposal_raw = os.getenv("AUTO_PROPOSAL_ENABLED", "true").strip().lower()
        if auto_proposal_raw not in {"true", "false"}:
            raise ValueError("AUTO_PROPOSAL_ENABLED must be true or false")
        resident_alert_notifications_raw = os.getenv(
            "RESIDENT_ALERT_NOTIFICATIONS_ENABLED",
            "false",
        ).strip().lower()
        if resident_alert_notifications_raw not in {"true", "false"}:
            raise ValueError("RESIDENT_ALERT_NOTIFICATIONS_ENABLED must be true or false")
        resident_alert_notification_cooldown_seconds = int(
            os.getenv("RESIDENT_ALERT_NOTIFICATION_COOLDOWN_SECONDS", "3600")
        )
        if not 60 <= resident_alert_notification_cooldown_seconds <= 86400:
            raise ValueError("RESIDENT_ALERT_NOTIFICATION_COOLDOWN_SECONDS must be between 60 and 86400")
        predictive_warning_policy_version = os.getenv(
            "PREDICTIVE_WARNING_POLICY_VERSION",
            "predictive-warning-policy-v1",
        ).strip()
        if not predictive_warning_policy_version:
            raise ValueError("PREDICTIVE_WARNING_POLICY_VERSION must not be empty")
        predictive_notifications_raw = os.getenv(
            "PREDICTIVE_WARNING_NOTIFICATIONS_ENABLED",
            "false",
        ).strip().lower()
        if predictive_notifications_raw not in {"true", "false"}:
            raise ValueError("PREDICTIVE_WARNING_NOTIFICATIONS_ENABLED must be true or false")
        predictive_evaluation_interval = int(
            os.getenv("PREDICTIVE_WARNING_EVALUATION_INTERVAL_SECONDS", "900")
        )
        if not 300 <= predictive_evaluation_interval <= 3600:
            raise ValueError("PREDICTIVE_WARNING_EVALUATION_INTERVAL_SECONDS must be between 300 and 3600")
        predictive_lead_minutes = int(os.getenv("PREDICTIVE_WARNING_LEAD_MINUTES", "45"))
        if not 15 <= predictive_lead_minutes <= 120:
            raise ValueError("PREDICTIVE_WARNING_LEAD_MINUTES must be between 15 and 120")
        predictive_lead_tolerance = int(
            os.getenv("PREDICTIVE_WARNING_LEAD_TOLERANCE_MINUTES", "15")
        )
        if not 0 <= predictive_lead_tolerance <= 30:
            raise ValueError("PREDICTIVE_WARNING_LEAD_TOLERANCE_MINUTES must be between 0 and 30")
        predictive_min_confidence = float(os.getenv("PREDICTIVE_WARNING_MIN_CONFIDENCE", "0.60"))
        if not 0 <= predictive_min_confidence <= 1:
            raise ValueError("PREDICTIVE_WARNING_MIN_CONFIDENCE must be between 0 and 1")
        predictive_forecast_max_age = int(
            os.getenv("PREDICTIVE_WARNING_FORECAST_MAX_AGE_SECONDS", "900")
        )
        if not 60 <= predictive_forecast_max_age <= 3600:
            raise ValueError("PREDICTIVE_WARNING_FORECAST_MAX_AGE_SECONDS must be between 60 and 3600")
        predictive_clear_evaluations = int(
            os.getenv("PREDICTIVE_WARNING_CLEAR_EVALUATIONS", "2")
        )
        if not 1 <= predictive_clear_evaluations <= 8:
            raise ValueError("PREDICTIVE_WARNING_CLEAR_EVALUATIONS must be between 1 and 8")
        proposal_pending_ttl_seconds = int(os.getenv("PROPOSAL_PENDING_TTL_SECONDS", "3600"))
        if proposal_pending_ttl_seconds <= 0:
            raise ValueError("PROPOSAL_PENDING_TTL_SECONDS must be positive")
        auto_proposal_stations = tuple(
            station.strip().upper()
            for station in os.getenv("AUTO_PROPOSAL_STATIONS", "").split(",")
            if station.strip()
        )
        invalid_stations = [station for station in auto_proposal_stations if station not in {"S01", "S02", "S03", "S04", "S05"}]
        if invalid_stations:
            raise ValueError(f"AUTO_PROPOSAL_STATIONS contains invalid station(s): {','.join(invalid_stations)}")

        trigger_seconds_raw = os.getenv("VENTILATION_TRIGGER_SECONDS", "").strip()
        legacy_trigger_minutes_raw = os.getenv("VENTILATION_TRIGGER_MINUTES", "").strip()
        ventilation_trigger_seconds = (
            int(trigger_seconds_raw)
            if trigger_seconds_raw
            else int(legacy_trigger_minutes_raw) * 60
            if legacy_trigger_minutes_raw
            else 15 * 60
        )
        ventilation_recovery_minutes = int(os.getenv("VENTILATION_RECOVERY_MINUTES", "20"))
        ventilation_safe_pm25_threshold = float(os.getenv("VENTILATION_SAFE_PM25_THRESHOLD", "25"))
        ventilation_safe_co2_threshold = float(os.getenv("VENTILATION_SAFE_CO2_THRESHOLD", "700"))
        ventilation_default_duration_minutes = int(os.getenv("VENTILATION_DEFAULT_DURATION_MINUTES", "45"))
        ventilation_intensity_percent = int(os.getenv("VENTILATION_INTENSITY_PERCENT", "80"))
        ventilation_max_gap_seconds = int(os.getenv("VENTILATION_MAX_GAP_SECONDS", "60"))
        if not 10 <= ventilation_trigger_seconds <= 7200:
            raise ValueError("VENTILATION_TRIGGER_SECONDS must be between 10 and 7200")
        if not 1 <= ventilation_recovery_minutes <= 180:
            raise ValueError("VENTILATION_RECOVERY_MINUTES must be between 1 and 180")
        if not 0 < ventilation_safe_pm25_threshold < warning:
            raise ValueError("VENTILATION_SAFE_PM25_THRESHOLD must be positive and below PM25_WARNING_THRESHOLD")
        if not 0 < ventilation_safe_co2_threshold < co2_warning:
            raise ValueError("VENTILATION_SAFE_CO2_THRESHOLD must be positive and below CO2_WARNING_THRESHOLD")
        if not 5 <= ventilation_default_duration_minutes <= 180:
            raise ValueError("VENTILATION_DEFAULT_DURATION_MINUTES must be between 5 and 180")
        if not 1 <= ventilation_intensity_percent <= 100:
            raise ValueError("VENTILATION_INTENSITY_PERCENT must be between 1 and 100")
        if not 1 <= ventilation_max_gap_seconds <= stale_after_seconds:
            raise ValueError("VENTILATION_MAX_GAP_SECONDS must be positive and no greater than STALE_AFTER_SECONDS")

        report_timezone = os.getenv("REPORT_TIMEZONE", "Asia/Ho_Chi_Minh").strip()
        try:
            ZoneInfo(report_timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("REPORT_TIMEZONE must be a valid IANA timezone") from exc
        report_policy_version = os.getenv("REPORT_POLICY_VERSION", "b7-esg-reports-v1").strip()
        if not report_policy_version:
            raise ValueError("REPORT_POLICY_VERSION must not be empty")
        report_expected_sample_interval_seconds = int(
            os.getenv("REPORT_EXPECTED_SAMPLE_INTERVAL_SECONDS", "10")
        )
        if not 1 <= report_expected_sample_interval_seconds <= 3600:
            raise ValueError("REPORT_EXPECTED_SAMPLE_INTERVAL_SECONDS must be between 1 and 3600")
        report_minimum_coverage_ratio = float(
            os.getenv("REPORT_MINIMUM_COVERAGE_RATIO", "0.75")
        )
        if not 0 < report_minimum_coverage_ratio <= 1:
            raise ValueError("REPORT_MINIMUM_COVERAGE_RATIO must be greater than 0 and at most 1")
        report_matrix_min_eligible_stations = int(
            os.getenv("REPORT_MATRIX_MIN_ELIGIBLE_STATIONS", "3")
        )
        if not 1 <= report_matrix_min_eligible_stations <= 5:
            raise ValueError("REPORT_MATRIX_MIN_ELIGIBLE_STATIONS must be between 1 and 5")
        report_narrative_endpoint = os.getenv("REPORT_NARRATIVE_ENDPOINT", "").strip() or None
        report_narrative_timeout_seconds = float(os.getenv("REPORT_NARRATIVE_TIMEOUT_SECONDS", "5"))
        if report_narrative_timeout_seconds <= 0:
            raise ValueError("REPORT_NARRATIVE_TIMEOUT_SECONDS must be positive")
        report_narrative_service_token = os.getenv("REPORT_NARRATIVE_SERVICE_TOKEN", "").strip() or None

        def _get_int(key: str, default: int) -> int:
            val = os.getenv(key)
            if val is None or not val.strip():
                return default
            return int(val.strip())

        session_ttl_seconds = _get_int("SESSION_TTL_SECONDS", 604800)
        if session_ttl_seconds <= 0:
            raise ValueError("SESSION_TTL_SECONDS must be positive")
        verification_token_ttl_seconds = _get_int("VERIFICATION_TOKEN_TTL_SECONDS", 86400)
        if verification_token_ttl_seconds <= 0:
            raise ValueError("VERIFICATION_TOKEN_TTL_SECONDS must be positive")
        reset_token_ttl_seconds = _get_int("RESET_TOKEN_TTL_SECONDS", 3600)
        if reset_token_ttl_seconds <= 0:
            raise ValueError("RESET_TOKEN_TTL_SECONDS must be positive")
        cookie_secure_raw = (os.getenv("COOKIE_SECURE") or "false").strip().lower()
        cookie_secure = cookie_secure_raw in {"true", "1", "yes"}
        cookie_samesite = (os.getenv("COOKIE_SAMESITE") or "lax").strip().lower()
        if cookie_samesite not in {"lax", "strict", "none"}:
            cookie_samesite = "lax"
        frontend_url = (os.getenv("FRONTEND_URL") or "http://localhost:5173").strip().rstrip("/")
        rate_limit_max = _get_int("RATE_LIMIT_LOGIN_MAX_ATTEMPTS", 5)
        rate_limit_lockout = _get_int("RATE_LIMIT_LOCKOUT_SECONDS", 900)

        demo_mode_raw = (os.getenv("AUTH_DEMO_MODE") or "true").strip().lower()
        auth_demo_mode = demo_mode_raw in {"true", "1", "yes"}

        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
        weather_api_base_url = os.getenv("WEATHER_API_BASE_URL", "").strip() or None
        weather_timeout_seconds = float(os.getenv("WEATHER_TIMEOUT_SECONDS", "3"))
        weather_latitude = float(os.getenv("WEATHER_LATITUDE", "20.993"))
        weather_longitude = float(os.getenv("WEATHER_LONGITUDE", "105.944"))
        weather_max_age_seconds = int(os.getenv("WEATHER_MAX_AGE_SECONDS", "3600"))
        if weather_timeout_seconds <= 0 or weather_max_age_seconds <= 0:
            raise ValueError("Weather timeout and max age must be positive")
        if not -90 <= weather_latitude <= 90 or not -180 <= weather_longitude <= 180:
            raise ValueError("Weather coordinates are invalid")

        return cls(
            database_url=os.getenv("DATABASE_URL"),
            cors_origins=[origin.strip() for origin in raw_origins.split(",") if origin.strip()],
            stale_after_seconds=stale_after_seconds,
            alert_warning_threshold=warning,
            alert_critical_threshold=critical,
            alert_rule_version=os.getenv("PM25_ALERT_RULE_VERSION", "pm25-threshold-v1"),
            alert_consecutive_measurements=consecutive,
            environmental_alert_rule_version=os.getenv("ENVIRONMENT_ALERT_RULE_VERSION", "environmental-threshold-v1"),
            aqi_warning_threshold=aqi_warning,
            aqi_critical_threshold=aqi_critical,
            co2_warning_threshold=co2_warning,
            co2_critical_threshold=co2_critical,
            noise_warning_threshold=noise_warning,
            noise_critical_threshold=noise_critical,
            temperature_warning_threshold=temperature_warning,
            temperature_critical_threshold=temperature_critical,
            agent_service_url=os.getenv("AGENT_SERVICE_URL", "http://localhost:8001").rstrip("/"),
            agent_service_timeout_seconds=agent_timeout,
            auto_proposal_enabled=auto_proposal_raw == "true",
            resident_alert_notifications_enabled=resident_alert_notifications_raw == "true",
            resident_alert_notification_cooldown_seconds=resident_alert_notification_cooldown_seconds,
            predictive_warning_policy_version=predictive_warning_policy_version,
            predictive_warning_notifications_enabled=predictive_notifications_raw == "true",
            predictive_warning_evaluation_interval_seconds=predictive_evaluation_interval,
            predictive_warning_lead_minutes=predictive_lead_minutes,
            predictive_warning_lead_tolerance_minutes=predictive_lead_tolerance,
            predictive_warning_min_confidence=predictive_min_confidence,
            predictive_warning_forecast_max_age_seconds=predictive_forecast_max_age,
            predictive_warning_clear_evaluations=predictive_clear_evaluations,
            proposal_pending_ttl_seconds=proposal_pending_ttl_seconds,
            auto_proposal_stations=auto_proposal_stations,
            ventilation_trigger_seconds=ventilation_trigger_seconds,
            ventilation_recovery_minutes=ventilation_recovery_minutes,
            ventilation_safe_pm25_threshold=ventilation_safe_pm25_threshold,
            ventilation_safe_co2_threshold=ventilation_safe_co2_threshold,
            ventilation_default_duration_minutes=ventilation_default_duration_minutes,
            ventilation_intensity_percent=ventilation_intensity_percent,
            ventilation_max_gap_seconds=ventilation_max_gap_seconds,
            report_timezone=report_timezone,
            report_policy_version=report_policy_version,
            report_expected_sample_interval_seconds=report_expected_sample_interval_seconds,
            report_minimum_coverage_ratio=report_minimum_coverage_ratio,
            report_matrix_min_eligible_stations=report_matrix_min_eligible_stations,
            report_narrative_endpoint=report_narrative_endpoint,
            report_narrative_timeout_seconds=report_narrative_timeout_seconds,
            report_narrative_service_token=report_narrative_service_token,
            session_ttl_seconds=session_ttl_seconds,
            verification_token_ttl_seconds=verification_token_ttl_seconds,
            reset_token_ttl_seconds=reset_token_ttl_seconds,
            cookie_secure=cookie_secure,
            cookie_samesite=cookie_samesite,
            frontend_url=frontend_url,
            rate_limit_login_max_attempts=rate_limit_max,
            rate_limit_lockout_seconds=rate_limit_lockout,
            auth_demo_mode=auth_demo_mode,
            google_client_id=google_client_id.strip() if google_client_id and google_client_id.strip() else None,
            google_client_secret=google_client_secret.strip() if google_client_secret and google_client_secret.strip() else None,
            google_redirect_uri=google_redirect_uri.strip() if google_redirect_uri and google_redirect_uri.strip() else None,
            weather_api_base_url=weather_api_base_url,
            weather_timeout_seconds=weather_timeout_seconds,
            weather_latitude=weather_latitude,
            weather_longitude=weather_longitude,
            weather_max_age_seconds=weather_max_age_seconds,
        )
