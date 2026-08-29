from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from .database import ServiceError
from .forecast_service import InsufficientForecastHistory, trend_forecast

INHALED_MASS_POLICY_VERSION = "inhaled-mass-policy-v1"
VENTILATION_RATE_M3_MIN = {
    "resting": Decimal("0.006"),
    "running": Decimal("0.045"),
}
DISCLAIMER = "Ước tính mô hình demo; không phải liều hấp thụ hoặc tư vấn y tế."


def _finite_decimal(value: Any, *, code: str, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ServiceError(code, f"{field} must be a finite non-negative number", 503)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ServiceError(code, f"{field} must be a finite non-negative number", 503) from exc
    if not math.isfinite(number) or number < 0:
        raise ServiceError(code, f"{field} must be a finite non-negative number", 503)
    return Decimal(str(value))


def _aware_datetime(value: Any, *, code: str, field: str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ServiceError(code, f"{field} must be a timezone-aware timestamp", 503) from exc
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ServiceError(code, f"{field} must be a timezone-aware timestamp", 503)
    return value.astimezone(UTC)


def calculate_estimated_inhaled_mass(
    *,
    pm25_ug_m3: Any,
    activity: str,
    duration_minutes: int | Decimal,
) -> Decimal:
    if activity not in VENTILATION_RATE_M3_MIN:
        raise ServiceError("invalid_activity", "activity must be resting or running", 422)
    if isinstance(duration_minutes, bool):
        raise ServiceError("invalid_duration", "duration_minutes must be between 1 and 180", 422)
    duration = _finite_decimal(duration_minutes, code="invalid_duration", field="duration_minutes")
    if duration < 1 or duration > 180:
        raise ServiceError("invalid_duration", "duration_minutes must be between 1 and 180", 422)
    concentration = _finite_decimal(
        pm25_ug_m3,
        code="environmental_data_unavailable",
        field="pm25_ug_m3",
    )
    return concentration * VENTILATION_RATE_M3_MIN[activity] * duration


def rounded_mass(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class InhaledDoseService:
    def __init__(
        self,
        station_service: Any,
        *,
        observation_max_age_seconds: int = 300,
        min_forecast_confidence: float = 0.60,
        forecast_max_age_seconds: int = 900,
        clock: Any | None = None,
    ) -> None:
        self.station_service = station_service
        self.observation_max_age_seconds = int(observation_max_age_seconds)
        self.min_forecast_confidence = float(min_forecast_confidence)
        self.forecast_max_age_seconds = int(forecast_max_age_seconds)
        self._clock = clock or (lambda: datetime.now(UTC))

    def estimate(
        self,
        *,
        station_id: str,
        activity: Literal["resting", "running"] | str,
        duration_minutes: int,
        data_mode: Literal["current", "forecast"] | str = "current",
        forecast_hour: int | None = None,
    ) -> dict[str, Any]:
        self._validate_mode(data_mode, forecast_hour)
        if activity not in VENTILATION_RATE_M3_MIN:
            raise ServiceError("invalid_activity", "activity must be resting or running", 422)
        if isinstance(duration_minutes, bool) or not isinstance(duration_minutes, int) or not 1 <= duration_minutes <= 180:
            raise ServiceError("invalid_duration", "duration_minutes must be an integer between 1 and 180", 422)

        concentration = (
            self._current_concentration(station_id)
            if data_mode == "current"
            else self._forecast_concentration(station_id, int(forecast_hour or 0))
        )
        mass = calculate_estimated_inhaled_mass(
            pm25_ug_m3=concentration["pm25_ug_m3"],
            activity=activity,
            duration_minutes=duration_minutes,
        )
        return {
            "station_id": station_id,
            "activity": activity,
            "duration_minutes": duration_minutes,
            "ventilation_rate_m3_min": float(VENTILATION_RATE_M3_MIN[activity]),
            "concentration": concentration,
            "estimated_inhaled_mass_ug": rounded_mass(mass),
            "formula": "pm25_ug_m3 * ventilation_rate_m3_min * duration_minutes",
            "policy_version": INHALED_MASS_POLICY_VERSION,
            "disclaimer": DISCLAIMER,
        }

    @staticmethod
    def _validate_mode(data_mode: str, forecast_hour: int | None) -> None:
        if data_mode not in {"current", "forecast"}:
            raise ServiceError("invalid_forecast_hour", "data_mode must be current or forecast", 422)
        if data_mode == "current" and forecast_hour is not None:
            raise ServiceError("invalid_forecast_hour", "forecast_hour must be null for current data", 422)
        if data_mode == "forecast" and (
            isinstance(forecast_hour, bool) or not isinstance(forecast_hour, int) or not 1 <= forecast_hour <= 3
        ):
            raise ServiceError("invalid_forecast_hour", "forecast_hour must be between 1 and 3", 422)

    def _current_concentration(self, station_id: str) -> dict[str, Any]:
        station = self.station_service.get_station(station_id)
        if (
            station.get("status") != "online"
            or station.get("freshness") != "fresh"
            or station.get("is_stale") is True
            or station.get("source") != "simulator"
            or station.get("pm25") is None
        ):
            raise ServiceError(
                "environmental_data_unavailable",
                "Fresh valid online simulator PM2.5 data is required",
                503,
                {"station_id": station_id, "quality_state": station.get("status") or "unavailable"},
            )
        observed_at = _aware_datetime(
            station.get("updated_at"),
            code="environmental_data_unavailable",
            field="observed_at",
        )
        observation_age = (self._clock().astimezone(UTC) - observed_at).total_seconds()
        if not 0 <= observation_age <= self.observation_max_age_seconds:
            raise ServiceError(
                "environmental_data_unavailable",
                "The latest valid PM2.5 measurement is stale",
                503,
                {"station_id": station_id, "quality_state": "stale"},
            )
        pm25 = _finite_decimal(
            station.get("pm25"),
            code="environmental_data_unavailable",
            field="pm25_ug_m3",
        )
        return {
            "pm25_ug_m3": float(pm25),
            "data_mode": "current",
            "observed_at": observed_at.isoformat(),
            "forecast_at": None,
            "source": "simulator",
            "model_version": None,
            "confidence": None,
            "quality_state": "valid",
        }

    def _forecast_concentration(self, station_id: str, forecast_hour: int) -> dict[str, Any]:
        # Current quality is a gate even when the numeric basis is a forecast.
        self._current_concentration(station_id)
        history = self.station_service.get_forecast_history(station_id)
        try:
            forecast = trend_forecast(history, forecast_hour, metric="pm25", generated_at=self._clock())
        except InsufficientForecastHistory as exc:
            raise ServiceError(
                "insufficient_forecast_quality",
                "Forecast history is insufficient",
                503,
                {"station_id": station_id},
            ) from exc
        generated_at = _aware_datetime(
            forecast.get("generated_at"),
            code="insufficient_forecast_quality",
            field="generated_at",
        )
        age = (self._clock().astimezone(UTC) - generated_at).total_seconds()
        confidence = float(forecast.get("confidence", -1))
        if (
            forecast.get("freshness") != "fresh"
            or age < 0
            or age > self.forecast_max_age_seconds
            or not math.isfinite(confidence)
            or confidence < self.min_forecast_confidence
        ):
            raise ServiceError(
                "insufficient_forecast_quality",
                "Forecast freshness or confidence does not pass policy",
                503,
                {"station_id": station_id},
            )
        items = forecast.get("items") or []
        point = next((item for item in items if item.get("hour_offset") == forecast_hour), None)
        if not point:
            raise ServiceError("insufficient_forecast_quality", "Forecast point is unavailable", 503)
        forecast_at = _aware_datetime(
            point.get("forecast_at"),
            code="insufficient_forecast_quality",
            field="forecast_at",
        )
        pm25 = _finite_decimal(
            point.get("value"),
            code="insufficient_forecast_quality",
            field="forecast_pm25_ug_m3",
        )
        source = str(point.get("source") or forecast.get("source") or "")
        model_version = str(forecast.get("model_version") or "")
        if not source or not model_version:
            raise ServiceError("insufficient_forecast_quality", "Forecast provenance is incomplete", 503)
        return {
            "pm25_ug_m3": float(pm25),
            "data_mode": "forecast",
            "observed_at": generated_at.isoformat(),
            "forecast_at": forecast_at.isoformat(),
            "source": source,
            "model_version": model_version,
            "confidence": confidence,
            "quality_state": "valid",
        }
