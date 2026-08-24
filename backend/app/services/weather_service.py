from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

import httpx


class WeatherService:
    """Open-Meteo current-weather adapter with an explicit simulator fallback."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        latitude: float = 20.993,
        longitude: float = 105.944,
        timeout_seconds: float = 3.0,
        max_age_seconds: int = 3600,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.latitude = latitude
        self.longitude = longitude
        self.timeout_seconds = timeout_seconds
        self.max_age_seconds = max_age_seconds
        self.transport = transport

    def current_weather(self) -> dict[str, object]:
        if not self.base_url:
            return self._fallback("provider_not_configured")
        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.get(
                    self.base_url,
                    params={
                        "latitude": self.latitude,
                        "longitude": self.longitude,
                        "current": (
                            "temperature_2m,relative_humidity_2m,precipitation,"
                            "wind_speed_10m,wind_direction_10m"
                        ),
                        "wind_speed_unit": "ms",
                        "timezone": "UTC",
                    },
                )
                response.raise_for_status()
                return self._parse_provider_payload(response.json())
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            return self._fallback("provider_unavailable_or_invalid")

    def _parse_provider_payload(self, payload: dict[str, Any]) -> dict[str, object]:
        current = payload["current"]
        observed_at = self._parse_time(current["time"])
        values = {
            "temperature": self._finite(current["temperature_2m"], "temperature_2m"),
            "humidity": self._finite(current["relative_humidity_2m"], "relative_humidity_2m"),
            "rainfall": self._finite(current["precipitation"], "precipitation"),
            "wind_speed": self._finite(current["wind_speed_10m"], "wind_speed_10m"),
            "wind_direction": self._finite(current["wind_direction_10m"], "wind_direction_10m"),
        }
        if not 0 <= values["humidity"] <= 100:
            raise ValueError("relative_humidity_2m is outside 0..100")
        if values["rainfall"] < 0 or not 0 <= values["wind_speed"] <= 100:
            raise ValueError("weather values are outside accepted ranges")
        if not 0 <= values["wind_direction"] <= 360:
            raise ValueError("wind_direction_10m is outside 0..360")
        age_seconds = max(0.0, (datetime.now(UTC) - observed_at).total_seconds())
        return {
            "area_id": "vinuni-ocean-park",
            **values,
            "wind_speed_ms": values["wind_speed"],
            "wind_direction_deg": values["wind_direction"],
            "source": "open_meteo_forecast_api",
            "observed_at": observed_at.isoformat(),
            "is_fallback": False,
            "is_stale": age_seconds > self.max_age_seconds,
        }

    @staticmethod
    def _parse_time(value: object) -> datetime:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _finite(value: object, name: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{name} must be finite")
        return number

    @staticmethod
    def _fallback(reason: str) -> dict[str, object]:
        return {
            "area_id": "vinuni-ocean-park",
            "temperature": 31.5,
            "humidity": 72.0,
            "wind_speed": 2.4,
            "wind_speed_ms": 2.4,
            "wind_direction": 135.0,
            "wind_direction_deg": 135.0,
            "rainfall": 0.0,
            "source": "simulator_fallback_weather",
            "observed_at": datetime.now(UTC).isoformat(),
            "is_fallback": True,
            "is_stale": False,
            "fallback_reason": reason,
        }
