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
            "status": "online",
            "level": "good",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S02": {
            "station_id": "S02",
            "pm25": 58.2,
            "status": "online",
            "level": "unhealthy",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S03": {
            "station_id": "S03",
            "pm25": 61.3,
            "status": "online",
            "level": "unhealthy",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S04": {
            "station_id": "S04",
            "pm25": 23.0,
            "status": "online",
            "level": "good",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
        "S05": {
            "station_id": "S05",
            "pm25": 35.5,
            "status": "online",
            "level": "moderate",
            "is_stale": False,
            "updated_at": FIXED_NOW.isoformat(),
            "source": "simulator",
        },
    },
    "alerts": {
        "items": [
            {
                "alert_id": "alert-S02-001",
                "station_id": "S02",
                "alert_type": "pm25_threshold",
                "severity": "warning",
                "observed_value": 58.2,
                "threshold_value": 50,
                "status": "active",
                "created_at": FIXED_NOW.isoformat(),
                "source": "fixture_alert_rule",
            }
        ]
    },
    "profiles": {
        "demo-user": {
            "user_id": "demo-user",
            "group": "normal",
            "display_name": "Demo User",
            "source": "fixture",
        }
    },
}


class FakeBackendToolClient:
    def __init__(self, fixtures: Mapping[str, Any] | None = None) -> None:
        self.fixtures = deepcopy(DEFAULT_FIXTURES)
        if fixtures:
            self.fixtures.update(deepcopy(fixtures))
        self.created_proposals: list[dict[str, Any]] = []

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
            current = self.fixtures["current"][args.station_id]
            items = [
                {
                    "station_id": args.station_id,
                    "measured_at": (FIXED_NOW - timedelta(hours=args.hours - offset)).isoformat(),
                    "pm25": max(1.0, current["pm25"] - 0.5 + offset * 0.1),
                    "source": current["source"],
                }
                for offset in range(args.hours)
            ]
            data = StationHistory.model_validate({"station_id": args.station_id, "hours": args.hours, "items": items}).model_dump(
                mode="json"
            )
        except KeyError:
            return self._error(ToolName.GET_STATION_HISTORY, request_id, ToolErrorCode.NOT_FOUND, "Station fixture not found.")
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
            self.created_proposals.append(args.model_dump(mode="json"))
            data = WarningProposal.model_validate(
                {"proposal_id": f"proposal-{len(self.created_proposals):03d}", "status": "pending", "request_id": request_id}
            ).model_dump(mode="json")
        except ValidationError as exc:
            return self._validation_error(ToolName.CREATE_WARNING_PROPOSAL, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.CREATE_WARNING_PROPOSAL, request_id=request_id, data=data)

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

