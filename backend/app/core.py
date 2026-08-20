from __future__ import annotations

import os
from dataclasses import dataclass


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
    proposal_pending_ttl_seconds: int
    auto_proposal_stations: tuple[str, ...]
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

    @classmethod
    def load(cls) -> Settings:
        raw_origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        stale_after_seconds = int(os.getenv("STALE_AFTER_SECONDS", "300"))
        if stale_after_seconds <= 0:
            raise ValueError("STALE_AFTER_SECONDS must be positive")

        warning = float(os.getenv("PM25_WARNING_THRESHOLD", "50"))
        critical = float(os.getenv("PM25_CRITICAL_THRESHOLD", "100"))
        if warning <= 0 or critical <= warning:
            raise ValueError("PM25 thresholds must satisfy 0 < warning < critical")
        consecutive = int(os.getenv("PM25_ALERT_CONSECUTIVE_MEASUREMENTS", "2"))
        if consecutive < 1 or consecutive > 20:
            raise ValueError("PM25_ALERT_CONSECUTIVE_MEASUREMENTS must be between 1 and 20")
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
            proposal_pending_ttl_seconds=proposal_pending_ttl_seconds,
            auto_proposal_stations=auto_proposal_stations,
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
        )
