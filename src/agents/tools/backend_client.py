from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError

from src.agents.tools.contracts import (
    TOOL_REGISTRY,
    ActiveAlertsInput,
    CompareStationsInput,
    CurrentPm25Input,
    ExtendedForecastInput,
    Pm25ForecastInput,
    SpatialAirQualityInput,
    StationComparison,
    StationHistoryInput,
    ToolEnvelope,
    ToolError,
    ToolErrorCode,
    ToolName,
    UserProfileInput,
    WarningProposalInput,
    WeatherContextInput,
)


class BackendToolClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 3.0,
        max_retries: int = 1,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> BackendToolClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds)
        return self

    async def __aexit__(self, *_exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    async def get_current_pm25(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = CurrentPm25Input.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_CURRENT_PM25, request_id, exc)
        return await self._request_and_validate(
            ToolName.GET_CURRENT_PM25,
            request_id,
            "GET",
            f"/api/v1/stations/{args.station_id}/current",
        )

    async def get_station_history(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = StationHistoryInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_STATION_HISTORY, request_id, exc)
        return await self._request_and_validate(
            ToolName.GET_STATION_HISTORY,
            request_id,
            "GET",
            f"/api/v1/stations/{args.station_id}/history",
            params={"hours": args.hours},
        )

    async def compare_stations(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = CompareStationsInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.COMPARE_STATIONS, request_id, exc)

        items: list[dict[str, Any]] = []
        for station_id in args.station_ids:
            result = await self._request_and_validate(
                ToolName.GET_CURRENT_PM25,
                request_id,
                "GET",
                f"/api/v1/stations/{station_id}/current",
            )
            if isinstance(result, ToolError):
                return ToolError(
                    tool_name=ToolName.COMPARE_STATIONS,
                    code=result.code,
                    message=result.message,
                    request_id=request_id,
                    status_code=result.status_code,
                    details={"station_id": station_id, **result.details},
                )
            items.append(result.data)

        try:
            data = StationComparison.model_validate({"items": items}).model_dump(mode="json")
        except ValidationError as exc:
            return self._schema_error(ToolName.COMPARE_STATIONS, request_id, exc)
        return ToolEnvelope(tool_name=ToolName.COMPARE_STATIONS, request_id=request_id, data=data)

    async def get_weather_context(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            WeatherContextInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_WEATHER_CONTEXT, request_id, exc)
        return await self._request_and_validate(
            ToolName.GET_WEATHER_CONTEXT,
            request_id,
            "GET",
            "/api/v1/weather/current",
        )

    async def get_pm25_forecast(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = Pm25ForecastInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_PM25_FORECAST, request_id, exc)
        return await self._request_and_validate(
            ToolName.GET_PM25_FORECAST,
            request_id,
            "GET",
            f"/api/v1/stations/{args.station_id}/forecast",
            params={"hours": args.hours},
        )

    async def get_extended_forecast(
        self, payload: Mapping[str, Any], request_id: str | None = None
    ) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = ExtendedForecastInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_EXTENDED_FORECAST, request_id, exc)
        return await self._request_and_validate(
            ToolName.GET_EXTENDED_FORECAST,
            request_id,
            "GET",
            f"/api/v1/stations/{args.station_id}/forecast",
            params={"hours": args.hours, "metric": args.metric, "model": "prophet"},
        )

    async def get_active_alerts(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = ActiveAlertsInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_ACTIVE_ALERTS, request_id, exc)
        params = {"status": "active"}
        if args.station_id is not None:
            params["station_id"] = args.station_id
        return await self._request_and_validate(
            ToolName.GET_ACTIVE_ALERTS,
            request_id,
            "GET",
            "/api/v1/alerts",
            params=params,
        )

    async def get_user_profile(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = UserProfileInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_USER_PROFILE, request_id, exc)
        return await self._request_and_validate(
            ToolName.GET_USER_PROFILE,
            request_id,
            "GET",
            f"/api/v1/users/{args.user_id}/profile",
        )

    async def create_warning_proposal(
        self, payload: Mapping[str, Any], request_id: str | None = None
    ) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = WarningProposalInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.CREATE_WARNING_PROPOSAL, request_id, exc)
        evidence_items: list[dict[str, Any]] = []
        ventilation_fields = {
            "alert_type",
            "ventilation_eligible",
            "ventilation_policy_version",
            "qualified_duration_seconds",
            "qualification_window_start",
            "qualification_window_end",
            "triggered_metrics",
        }
        for item in args.evidence:
            serialized = item.model_dump(mode="json")
            for field in ventilation_fields:
                if serialized.get(field) in (None, []):
                    serialized.pop(field, None)
            evidence_items.append(serialized)

        evidence_payload: dict[str, Any] = {
            "items": evidence_items,
            "target": args.target.model_dump(mode="json"),
            "policy_version": args.policy_version,
            "requested_by": args.user_id,
            "expires_at": args.expires_at.isoformat() if args.expires_at else None,
        }
        if args.action in {"ventilation_boost", "air_purifier_on", "eco_mode"}:
            evidence_payload["control"] = {
                "action": args.action,
                "duration_minutes": args.duration_minutes,
                "intensity_percent": args.intensity_percent,
                "mapping_source": "backend_device_registry",
            }

        backend_payload = {
            "request_type": "warning_proposal",
            "station_id": args.target.station_id,
            "proposed_action": args.action,
            "reason": args.rationale,
            "evidence": evidence_payload,
            "created_by": "ai_agent",
        }
        return await self._request_and_validate(
            ToolName.CREATE_WARNING_PROPOSAL,
            request_id,
            "POST",
            "/api/v1/proposals",
            json=backend_payload,
            headers={"Idempotency-Key": args.idempotency_key},
            max_retries=0,
        )

    async def get_spatial_air_quality(self, payload: Mapping[str, Any], request_id: str | None = None) -> ToolEnvelope | ToolError:
        request_id = request_id or self._new_request_id()
        try:
            args = SpatialAirQualityInput.model_validate(payload)
        except ValidationError as exc:
            return self._validation_error(ToolName.GET_SPATIAL_AIR_QUALITY, request_id, exc)
        return await self._request_and_validate(
            ToolName.GET_SPATIAL_AIR_QUALITY,
            request_id,
            "GET",
            "/api/v1/spatial/heatmap",
            params={"metric": args.metric, "forecast_hour": args.forecast_hour},
        )

    async def _request_and_validate(
        self,
        tool_name: ToolName,
        request_id: str,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_retries: int | None = None,
    ) -> ToolEnvelope | ToolError:
        client = self._client or httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds)
        should_close = self._client is None
        attempts = (self.max_retries if max_retries is None else max_retries) + 1
        try:
            for attempt in range(attempts):
                try:
                    request_headers = {"X-Request-ID": request_id, **(headers or {})}
                    response = await client.request(
                        method,
                        path,
                        params=params,
                        json=json,
                        headers=request_headers,
                    )
                except httpx.TimeoutException:
                    if attempt + 1 < attempts:
                        continue
                    return ToolError(
                        tool_name=tool_name,
                        code=ToolErrorCode.TIMEOUT,
                        message="Backend tool request timed out.",
                        request_id=request_id,
                    )
                except httpx.HTTPError as exc:
                    if attempt + 1 < attempts:
                        continue
                    return ToolError(
                        tool_name=tool_name,
                        code=ToolErrorCode.UNAVAILABLE,
                        message="Backend tool request failed.",
                        request_id=request_id,
                        details={"error": exc.__class__.__name__},
                    )

                if response.status_code >= 500 and attempt + 1 < attempts:
                    continue
                if response.status_code >= 400:
                    return self._http_error(tool_name, request_id, response)
                try:
                    raw = response.json()
                except ValueError:
                    return ToolError(
                        tool_name=tool_name,
                        code=ToolErrorCode.MALFORMED_RESPONSE,
                        message="Backend returned non-JSON tool output.",
                        request_id=request_id,
                        status_code=response.status_code,
                    )
                return self._validate_output(tool_name, request_id, raw)
        finally:
            if should_close:
                await client.aclose()

        return ToolError(
            tool_name=tool_name,
            code=ToolErrorCode.UNAVAILABLE,
            message="Backend tool request failed without a response.",
            request_id=request_id,
        )

    def _validate_output(self, tool_name: ToolName, request_id: str, raw: Any) -> ToolEnvelope | ToolError:
        try:
            data = TOOL_REGISTRY[tool_name].output_schema.model_validate(raw).model_dump(mode="json")
        except ValidationError as exc:
            return self._schema_error(tool_name, request_id, exc)
        return ToolEnvelope(tool_name=tool_name, request_id=request_id, data=data)

    def _http_error(self, tool_name: ToolName, request_id: str, response: httpx.Response) -> ToolError:
        code = ToolErrorCode.NOT_FOUND if response.status_code == 404 else ToolErrorCode.UNAVAILABLE
        if response.status_code in {401, 403}:
            code = ToolErrorCode.PERMISSION_DENIED
        if response.status_code == 422:
            code = ToolErrorCode.VALIDATION_ERROR
        message = "Backend tool endpoint returned an error."
        details: dict[str, Any] = {}
        try:
            body = response.json()
            details["body"] = body
            if isinstance(body, dict):
                message = str(body.get("message") or body.get("detail") or message)
        except ValueError:
            details["body"] = response.text[:200]
        return ToolError(
            tool_name=tool_name,
            code=code,
            message=message,
            request_id=request_id,
            status_code=response.status_code,
            details=details,
        )

    def _validation_error(self, tool_name: ToolName, request_id: str, exc: ValidationError) -> ToolError:
        return ToolError(
            tool_name=tool_name,
            code=ToolErrorCode.VALIDATION_ERROR,
            message="Tool input failed validation.",
            request_id=request_id,
            details={"errors": exc.errors()},
        )

    def _schema_error(self, tool_name: ToolName, request_id: str, exc: ValidationError) -> ToolError:
        return ToolError(
            tool_name=tool_name,
            code=ToolErrorCode.SCHEMA_DRIFT,
            message="Backend tool output did not match the registered schema.",
            request_id=request_id,
            details={"errors": exc.errors()},
        )

    def _new_request_id(self) -> str:
        return f"agent-tool-{uuid4()}"

