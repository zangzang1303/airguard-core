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
    Pm25Forecast,
    Pm25ForecastInput,
    SpatialAirQuality,
    SpatialAirQualityInput,
    StationComparison,
    StationHistory,
    StationHistoryInput,
    StationMeasurement,
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
                "station_id": "S01",
                "measured_at": (FIXED_NOW - timedelta(hours=idx)).isoformat(),
                "pm25": 20.0 + idx * 0.5,
                "co2": 600.0 + idx * 10,
                "noise_db": 50.0 + idx,
                "temperature": 28.0 + idx * 0.2,
                "quality_flag": "valid",
                "source": "simulator",
            }
            for idx in reversed(range(24))
        ],
    },
    "alerts": {
        "items": [
            {
                "alert_id": "alert-S02-001",
                "station_id": "S02",
                "alert_type": "pm25_threshold",
                "rule_version": "fixture-alert-rule-v1",
                "severity": "critical",
                "observed_value": 58.2,
                "threshold_value": 50.0,
                "status": "active",
                "created_at": FIXED_NOW.isoformat(),
                "source": "fixture_alert_rule",
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
            points = self.fixtures["history"].get(args.station_id)
            if points is None:
                points = [
                    {**point, "station_id": args.station_id}
                    for point in self.fixtures["history"]["S01"]
                ]
            points = points[-args.hours :]
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
            base = current["aqi"] if args.metric == "aqi" else current["pm25"]
            items = [
                {"hour": hour, "forecast_at": (FIXED_NOW + timedelta(hours=hour)).isoformat(), "value": round(base + hour * 0.8, 2), "value_min": round(base + hour * 0.3, 2), "value_max": round(base + hour * 1.3, 2), "confidence": 0.7, "source": "fixture_forecast"}
                for hour in range(1, args.hours + 1)
            ]
            data = Pm25Forecast.model_validate(
                {"station_id": args.station_id, "metric": args.metric, "horizon_hours": args.hours, "generated_at": FIXED_NOW.isoformat(), "model_name": "damped_linear_trend_v1", "model_version": "damped_linear_trend_v1", "source": "fixture_forecast", "freshness": "fresh", "is_stale": False, "confidence": 0.7, "limitations": ["Fixture simulator forecast."], "items": items}
            ).model_dump(mode="json")
        except KeyError:
            return self._error(ToolName.GET_PM25_FORECAST, request_id, ToolErrorCode.NOT_FOUND, "Station fixture not found.")
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_PM25_FORECAST, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.GET_PM25_FORECAST, request_id=request_id, data=data)

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
                "generated_at": FIXED_NOW.isoformat(),
                "forecast_hour": args.forecast_hour,
                "source": "spatial_idw_dispersion_model",
                "model_version": "idw-dispersion-v2.0",
                "model": {
                    "name": "wind_adjusted_inverse_distance_weighting",
                    "version": "idw-dispersion-v2.0",
                    "grid_rows": 30,
                    "grid_columns": 30,
                    "power": 2.0,
                    "minimum_stations": 3,
                },
                "extent": {
                    "south": 20.9840,
                    "west": 105.9330,
                    "north": 21.0050,
                    "east": 105.9630,
                },
                "wind_speed_ms": 3.2,
                "wind_direction_deg": 135,
                "weather": {
                    "wind_speed_ms": 3.2,
                    "wind_direction_deg": 135,
                    "source": "simulator_fallback_weather",
                    "observed_at": FIXED_NOW.isoformat(),
                    "is_fallback": True,
                    "is_stale": False,
                    "assumptions": ["wind_direction_uses_documented_simulator_assumption"],
                },
                "data_quality": {
                    "status": "valid",
                    "stations_required": 3,
                    "stations_used": ["S01", "S02", "S03", "S04", "S05"],
                    "stations_excluded": [],
                    "exclusion_reasons": {},
                    "station_sources": ["simulator"],
                    "forecast_sources": [],
                },
                "station_inputs": [
                    {
                        "station_id": station_id,
                        "lat": latitude,
                        "lon": longitude,
                        "value": value,
                        "source": "simulator",
                        "observed_at": FIXED_NOW.isoformat(),
                        "forecast_source": None,
                    }
                    for station_id, latitude, longitude, value in (
                        ("S01", 21.0008, 105.9428, 95.0),
                        ("S02", 20.9975, 105.9430, 90.0),
                        ("S03", 20.9953, 105.9500, 80.0),
                        ("S04", 20.9898, 105.9467, 68.0),
                        ("S05", 20.9910, 105.9560, 110.0),
                    )
                ],
                "grid_points": [
                    {
                        "lat": 20.9935,
                        "lon": 105.9405,
                        "value": 68.0,
                        "intensity": 0.272,
                        "level": "moderate",
                    },
                    {
                        "lat": 20.9938,
                        "lon": 105.9485,
                        "value": 72.4,
                        "intensity": 0.29,
                        "level": "moderate",
                    },
                    {
                        "lat": 20.9945,
                        "lon": 105.9585,
                        "value": 115.8,
                        "intensity": 0.463,
                        "level": "unhealthy_sensitive",
                    },
                    {
                        "lat": 21.0008,
                        "lon": 105.9428,
                        "value": 95.0,
                        "intensity": 0.38,
                        "level": "moderate",
                    },
                    {
                        "lat": 20.9975,
                        "lon": 105.9430,
                        "value": 90.0,
                        "intensity": 0.36,
                        "level": "moderate",
                    },
                    {
                        "lat": 20.9953,
                        "lon": 105.9500,
                        "value": 80.0,
                        "intensity": 0.32,
                        "level": "moderate",
                    },
                    {
                        "lat": 20.9910,
                        "lon": 105.9560,
                        "value": 110.0,
                        "intensity": 0.44,
                        "level": "unhealthy_sensitive",
                    },
                ],
                "disclaimer": "Mô hình nội suy trực quan hóa IDW kết hợp vector khí tượng mô phỏng.",
            }
            data = SpatialAirQuality.model_validate(data).model_dump(mode="json")
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
