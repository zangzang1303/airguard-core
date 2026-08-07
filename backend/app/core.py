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

    @classmethod
    def load(cls) -> "Settings":
        raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        stale_after_seconds = int(os.getenv("STALE_AFTER_SECONDS", "300"))
        if stale_after_seconds <= 0:
            raise ValueError("STALE_AFTER_SECONDS must be positive")

        warning = float(os.getenv("PM25_WARNING_THRESHOLD", "50"))
        critical = float(os.getenv("PM25_CRITICAL_THRESHOLD", "100"))
        if warning <= 0 or critical <= warning:
            raise ValueError("PM25 thresholds must satisfy 0 < warning < critical")

        return cls(
            database_url=os.getenv("DATABASE_URL"),
            cors_origins=[origin.strip() for origin in raw_origins.split(",") if origin.strip()],
            stale_after_seconds=stale_after_seconds,
            alert_warning_threshold=warning,
            alert_critical_threshold=critical,
            alert_rule_version=os.getenv("PM25_ALERT_RULE_VERSION", "pm25-threshold-v1"),
        )
