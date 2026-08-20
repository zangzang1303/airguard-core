from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import ValidationError

from src.agents.tools.contracts import (
    ActiveAlerts,
    ActiveAlertsInput,
    CompareStationsInput,
    CurrentPm25Input,
    ExtendedForecast,
    ExtendedForecastInput,
    Pm25Forecast,
    Pm25ForecastInput,
    StationComparison,
    StationHistory,
    StationHistoryInput,
    StationMeasurement,
    SpatialAirQualityInput,
    ToolEnvelope,
    ToolError,
    ToolErrorCode,
    ToolName,
    UserProfile,
    UserProfileInput,
    WarningProposal,
    WarningProposalInput,
    WeatherContext,
    WeatherContextInput,
)

FIXED_NOW = datetime(2026, 8, 4, 9, 0, tzinfo=timezone(timedelta(hours=7)))

DEFAULT_FIXTURES: dict[str, Any] = {
    "current": {
        "S01": {
            "station_id": "S01",
            "pm25": 22.4,
            "aqi": 72,
            "aqi_category": "moderate",
            "co2": 640.0,
            "noise_db": 54.0,
            "temperature": 30.0,
            "status": "online",
            "level": "good",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S02": {
            "station_id": "S02",
            "pm25": 58.2,
            "aqi": 151,
            "aqi_category": "unhealthy",
            "co2": 1080.0,
            "noise_db": 78.0,
            "temperature": 35.2,
            "status": "online",
            "level": "unhealthy",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S03": {
            "station_id": "S03",
            "pm25": 61.3,
            "aqi": 154,
            "aqi_category": "unhealthy",
            "co2": 930.0,
            "noise_db": 71.0,
            "temperature": 32.0,
            "status": "online",
            "level": "unhealthy",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S04": {
            "station_id": "S04",
            "pm25": 23.0,
            "aqi": 74,
            "aqi_category": "moderate",
            "co2": 570.0,
            "noise_db": 48.0,
            "temperature": 29.0,
            "status": "online",
            "level": "good",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S05": {
            "station_id": "S05",
            "pm25": 35.5,
            "aqi": 101,
            "aqi_category": "unhealthy_sensitive",
            "co2": 620.0,
            "noise_db": 55.0,
            "temperature": 30.0,
            "status": "online",
            "level": "moderate",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
    },
    "history": {
        "S01": [
            {
                "measured_at": (FIXED_NOW - timedelta(hours=idx)).isoformat(),
                "pm25": 20.0 + idx * 0.5,
                "co2": 600.0 + idx * 10,
                "noise_db": 50.0 + idx,
                "temperature": 28.0 + idx * 0.2,
                "quality_flag": "valid",
                "source": "simulator",
            }
            for idx in range(24)
        ],
    },
    "alerts": {
        "items": [
            {
                "alert_id": "ALT-001",
                "station_id": "S02",
                "alert_type": "pm25_threshold",
                "severity": "critical",
                "observed_value": 58.2,
                "threshold_value": 50.0,
                "status": "active",
                "created_at": FIXED_NOW.isoformat(),
                "source": "simulator",
                "title": "PM2.5 exceeded threshold",
                "description": "High particulate level recorded.",
                "unit": "ug/m3",
                "recommendation": "Wear masks and limit outdoor sports.",
            }
        ]
    },
    "profiles": {
        "demo-user": {
            "user_id": "demo-user",
            "user_group": "normal",
            "display_name": "Demo User",
            "source": "fixture",
        },
        "normal-user": {
            "user_id": "normal-user",
            "user_group": "normal",
            "display_name": "Normal User",
            "source": "fixture",
        },
        "sensitive-user": {
            "user_id": "sensitive-user",
            "user_group": "sensitive",
            "display_name": "Sensitive User",
            "source": "fixture",
        },
        "outdoor-user": {
            "user_id": "outdoor-user",
            "user_group": "outdoor_sport",
            "display_name": "Outdoor User",
            "source": "fixture",
        },
    },
}


class FakeBackendToolClient:
    def __init__(self, fixtures: Mapping[str, Any] | None = None) -> None:
        self.fixtures = deepcopy(DEFAULT_FIXTURES)
        if fixtures:
            self.fixtures.update(deepcopy(fixtures))
        self.created_proposals: list[dict[str, Any]] = []
        self._proposals_by_key: dict[str, dict[str, Any]] = {}

    async def get_current_pm25(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            args = CurrentPm25Input.model_validate(payload)
            data = StationMeasurement.model_validate(self.fixtures["current"][args.station_id]).model_dump(mode="json")
        except KeyError:
            return self._error(ToolName.GET_CURRENT_PM25, request_id, ToolErrorCode.NOT_FOUND, "Station fixture not found.")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_CURRENT_PM25, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_CURRENT_PM25, request_id=request_id, data=data)

    async def get_station_history(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            args = StationHistoryInput.model_validate(payload)
            points = self.fixtures["history"].get(args.station_id, self.fixtures["history"]["S01"])[: args.hours]
            data = StationHistory.model_validate({"station_id": args.station_id, "hours": args.hours, "items": points}).model_dump(mode="json")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_STATION_HISTORY, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_STATION_HISTORY, request_id=request_id, data=data)

    async def compare_stations(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            args = CompareStationsInput.model_validate(payload)
            items = [self.fixtures["current"][station_id] for station_id in args.station_ids]
            data = StationComparison.model_validate({"items": items}).model_dump(mode="json")
        except KeyError:
            return self._error(ToolName.COMPARE_STATIONS, request_id, ToolErrorCode.NOT_FOUND, "Station fixture not found.")
        except ValidationError as exc:
            return self._validation_error(ToolName.COMPARE_STATIONS, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.COMPARE_STATIONS, request_id=request_id, data=data)

    async def get_weather_context(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            WeatherContextInput.model_validate(payload)
            data = WeatherContext.model_validate(
                {
                    "area_id": "vinuni-ocean-park",
                    "temperature": 31.5,
                    "humidity": 72,
                    "wind_speed": 2.4,
                    "rainfall": 0,
                    "observed_at": FIXED_NOW.isoformat(),
                    "source": "fixture_weather",
                    "is_fallback": False,
                    "is_stale": False,
                }
            ).model_dump(mode="json")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_WEATHER_CONTEXT, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_WEATHER_CONTEXT, request_id=request_id, data=data)

    async def get_pm25_forecast(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            args = Pm25ForecastInput.model_validate(payload)
            current = self.fixtures["current"][args.station_id]
            items = [
                {"hour": hour, "pm25": round(current["pm25"] + hour * 0.8, 2), "confidence": 0.7, "source": "fixture_forecast"}
                for hour in range(1, args.hours + 1)
            ]
            data = Pm25Forecast.model_validate({"station_id": args.station_id, "items": items}).model_dump(mode="json")
        except KeyError:
            return self._error(ToolName.GET_PM25_FORECAST, request_id, ToolErrorCode.NOT_FOUND, "Station fixture not found.")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_PM25_FORECAST, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_PM25_FORECAST, request_id=request_id, data=data)

    async def get_extended_forecast(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            args = ExtendedForecastInput.model_validate(payload)
            current = self.fixtures["current"][args.station_id]
            base = float(current.get("pm25") or 40.0)
            horizons = [
                {
                    "hours_ahead": h,
                    "timestamp": (FIXED_NOW + timedelta(hours=h)).isoformat(),
                    "predicted_value": round(base + (h % 5 - 2) * 1.5, 1),
                    "lower_bound": round(base * 0.85, 1),
                    "upper_bound": round(base * 1.15, 1),
                    "confidence": 0.88,
                }
                for h in range(1, args.hours + 1)
            ]
            data = ExtendedForecast.model_validate({
                "station_id": args.station_id,
                "metric": args.metric,
                "model": "prophet_time_series_v1",
                "trend_summary": "Dự kiến chất lượng không khí duy trì ổn định.",
                "confidence": "high",
                "horizons": horizons,
            }).model_dump(mode="json")
        except KeyError:
            return self._error(ToolName.GET_EXTENDED_FORECAST, request_id, ToolErrorCode.NOT_FOUND, "Station fixture not found.")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_EXTENDED_FORECAST, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_EXTENDED_FORECAST, request_id=request_id, data=data)

    async def get_active_alerts(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            args = ActiveAlertsInput.model_validate(payload)
            items = self.fixtures["alerts"]["items"]
            if args.station_id:
                items = [item for item in items if item["station_id"] == args.station_id]
            data = ActiveAlerts.model_validate({"items": items}).model_dump(mode="json")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_ACTIVE_ALERTS, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_ACTIVE_ALERTS, request_id=request_id, data=data)

    async def get_user_profile(self, payload: Mapping[str, Any], request_id: str = "fixture-request") -> ToolEnvelope | ToolError:
        try:
            args = UserProfileInput.model_validate(payload)
            data = UserProfile.model_validate(self.fixtures["profiles"][args.user_id]).model_dump(mode="json")
        except KeyError:
            return self._error(ToolName.GET_USER_PROFILE, request_id, ToolErrorCode.NOT_FOUND, "User profile fixture not found.")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_USER_PROFILE, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_USER_PROFILE, request_id=request_id, data=data)

    async def create_warning_proposal(
        self, payload: Mapping[str, Any], request_id: str = "fixture-request"
    ) -> ToolEnvelope | ToolError:
        try:
            args = WarningProposalInput.model_validate(payload)
            data = self._proposals_by_key.get(args.idempotency_key)
            if data is None:
                self.created_proposals.append(args.model_dump(mode="json"))
                data = {
                    "request_id": f"proposal-{len(self.created_proposals):03d}",
                    "status": "pending",
                }
                self._proposals_by_key[args.idempotency_key] = data
            data = WarningProposal.model_validate(data).model_dump(mode="json")
        except ValidationError as exc:
            return self._validation_error(ToolName.CREATE_WARNING_PROPOSAL, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.CREATE_WARNING_PROPOSAL, request_id=request_id, data=data)

    async def get_spatial_air_quality(
        self, payload: Mapping[str, Any], request_id: str = "fixture-request"
    ) -> ToolEnvelope | ToolError:
        try:
            args = SpatialAirQualityInput.model_validate(payload)
            metric = args.metric.lower()
            data = {
                "metric": metric,
                "unit": "AQI" if metric == "aqi" else "µg/m³" if metric == "pm25" else "ppm" if metric == "co2" else "°C" if metric == "temperature" else "dB",
                "timestamp": FIXED_NOW.isoformat(),
                "forecast_hour": args.forecast_hour,
                "source": "spatial_idw_dispersion_model",
                "model_version": "idw-dispersion-v1.0",
                "wind_speed_ms": 3.2,
                "wind_direction_deg": 135,
                "grid_points": [
                    {"lat": 20.9912, "lon": 105.9521, "value": 72.4, "level": "moderate"},
                    {"lat": 20.9915, "lon": 105.9525, "value": 115.8, "level": "unhealthy_sensitive"},
                ],
                "disclaimer": "Mô hình nội suy trực quan hóa IDW kết hợp vector khí tượng mô phỏng.",
            }
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_SPATIAL_AIR_QUALITY, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_SPATIAL_AIR_QUALITY, request_id=request_id, data=data)

    def _validation_error(self, tool_name: ToolName, request_id: str, exc: ValidationError) -> ToolError:
        return ToolError(
            tool_name=tool_name,
            code=ToolErrorCode.VALIDATION_ERROR,
            message="Tool input failed validation.",
            request_id=request_id,
            details={"errors": exc.errors()},
        )

    def _error(self, tool_name: ToolName, request_id: str, code: ToolErrorCode, message: str) -> ToolError:
        return ToolError(tool_name=tool_name, code=code, message=message, request_id=request_id)
