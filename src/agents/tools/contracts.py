from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    field_validator,
    model_validator,
)

TOOL_REGISTRY_VERSION = "2026-08-21.ai-spatial-003"
TOOL_REGISTRY_OWNER = "ai-agent"
STATION_IDS = {"S01", "S02", "S03", "S04", "S05"}


class ToolName(StrEnum):
    GET_CURRENT_PM25 = "get_current_pm25"
    GET_STATION_HISTORY = "get_station_history"
    COMPARE_STATIONS = "compare_stations"
    GET_WEATHER_CONTEXT = "get_weather_context"
    GET_PM25_FORECAST = "get_pm25_forecast"
    GET_EXTENDED_FORECAST = "get_extended_forecast"
    GET_ACTIVE_ALERTS = "get_active_alerts"
    GET_USER_PROFILE = "get_user_profile"
    CREATE_WARNING_PROPOSAL = "create_warning_proposal"
    GET_SPATIAL_AIR_QUALITY = "get_spatial_air_quality"


class ToolErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "backend_unavailable"
    TIMEOUT = "backend_timeout"
    MALFORMED_RESPONSE = "malformed_response"
    SCHEMA_DRIFT = "schema_drift"
    UNSUPPORTED_ENDPOINT = "unsupported_endpoint"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class BackendOutputModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


def validate_station_id(value: str) -> str:
    normalized = value.upper()
    if normalized not in STATION_IDS:
        raise ValueError("station_id must be one of S01, S02, S03, S04, S05")
    return normalized


class ToolError(StrictModel):
    ok: Literal[False] = False
    tool_name: ToolName
    code: ToolErrorCode
    message: str
    request_id: str
    status_code: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ToolEnvelope(StrictModel):
    ok: Literal[True] = True
    tool_name: ToolName
    request_id: str
    data: dict[str, Any]


class CurrentPm25Input(StrictModel):
    station_id: str

    @field_validator("station_id")
    @classmethod
    def station_id_known(cls, value: str) -> str:
        return validate_station_id(value)


class StationHistoryInput(CurrentPm25Input):
    hours: int = Field(default=24, ge=1, le=72)


class CompareStationsInput(StrictModel):
    station_ids: list[str] = Field(..., min_length=2, max_length=5)

    @field_validator("station_ids")
    @classmethod
    def stations_known_and_unique(cls, values: list[str]) -> list[str]:
        normalized = [validate_station_id(value) for value in values]
        if len(set(normalized)) != len(normalized):
            raise ValueError("station_ids must be unique")
        return normalized


class WeatherContextInput(StrictModel):
    area_id: str = Field(default="vinuni-ocean-park", min_length=3, max_length=80)


class Pm25ForecastInput(CurrentPm25Input):
    hours: int = Field(default=3, ge=1, le=3)


class ActiveAlertsInput(StrictModel):
    station_id: str | None = None

    @field_validator("station_id")
    @classmethod
    def optional_station_known(cls, value: str | None) -> str | None:
        return validate_station_id(value) if value else value


class UserProfileInput(StrictModel):
    user_id: str = Field(..., min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:@-]+$")


class ProposalTarget(StrictModel):
    audience: Literal["normal", "sensitive", "outdoor_sport", "manager", "station_area"]
    station_id: str | None = None

    @field_validator("station_id")
    @classmethod
    def optional_station_known(cls, value: str | None) -> str | None:
        return validate_station_id(value) if value else value


class ProposalEvidence(StrictModel):
    source_tool: ToolName
    evidence_id: str | None = Field(default=None, min_length=1, max_length=120)
    station_id: str | None = None
    aqi: int | None = Field(default=None, ge=0, le=500)
    aqi_category: str | None = Field(default=None, min_length=1, max_length=80)
    pm25: float | None = Field(default=None, ge=0)
    co2: float | None = Field(default=None, ge=0)
    noise_db: float | None = Field(default=None, ge=0)
    temperature: float | None = None
    observed_value: float | None = Field(default=None, ge=0)
    threshold_value: float | None = Field(default=None, ge=0)
    measured_at: AwareDatetime | None = None
    source: str | None = None
    rule_version: str | None = Field(default=None, min_length=1, max_length=100)
    severity: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("station_id")
    @classmethod
    def optional_station_known(cls, value: str | None) -> str | None:
        return validate_station_id(value) if value else value


class WarningProposalInput(StrictModel):
    user_id: str = Field(..., min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:@-]+$")
    idempotency_key: str = Field(..., min_length=8, max_length=200)
    target: ProposalTarget
    action: str = Field(..., min_length=5, max_length=100)
    rationale: str = Field(..., min_length=10, max_length=1000)
    policy_version: str = Field(..., min_length=3, max_length=80)
    evidence: list[ProposalEvidence] = Field(..., min_length=1, max_length=10)
    expires_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def evidence_has_station_context(self) -> WarningProposalInput:
        if self.target.station_id is None:
            raise ValueError("warning proposal target requires station_id")
        if self.target.station_id and not any(item.station_id == self.target.station_id for item in self.evidence):
            raise ValueError("proposal evidence must include the target station_id")
        return self


class StationMeasurement(BackendOutputModel):
    station_id: str
    pm25: float = Field(..., ge=0)
    aqi: int | None = Field(default=None, ge=0, le=500)
    aqi_category: str | None = Field(default=None, min_length=1, max_length=80)
    co2: float | None = Field(default=None, ge=0)
    noise_db: float | None = Field(default=None, ge=0)
    temperature: float | None = None
    status: Literal["online", "offline", "stale", "invalid"]
    level: str | None = None
    is_stale: bool
    updated_at: AwareDatetime
    source: str = Field(..., min_length=1, max_length=100)

    @field_validator("station_id")
    @classmethod
    def station_id_known(cls, value: str) -> str:
        return validate_station_id(value)


class HistoryPoint(BackendOutputModel):
    station_id: str
    measured_at: AwareDatetime
    pm25: float = Field(..., ge=0)
    source: str = Field(..., min_length=1, max_length=100)

    @field_validator("station_id")
    @classmethod
    def station_id_known(cls, value: str) -> str:
        return validate_station_id(value)


class StationHistory(BackendOutputModel):
    station_id: str
    hours: int = Field(..., ge=1, le=72)
    items: list[HistoryPoint]

    @field_validator("station_id")
    @classmethod
    def station_id_known(cls, value: str) -> str:
        return validate_station_id(value)

    @model_validator(mode="after")
    def points_match_station_and_are_ordered(self) -> StationHistory:
        if any(item.station_id != self.station_id for item in self.items):
            raise ValueError("history points must match the requested station_id")
        timestamps = [item.measured_at for item in self.items]
        if timestamps != sorted(timestamps):
            raise ValueError("history points must be ordered by measured_at ascending")
        return self


class StationComparison(BackendOutputModel):
    items: list[StationMeasurement] = Field(..., min_length=2, max_length=5)


class WeatherContext(BackendOutputModel):
    area_id: str
    temperature: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    rainfall: float | None = None
    observed_at: AwareDatetime
    source: str = Field(..., min_length=1, max_length=100)
    is_fallback: bool
    is_stale: bool


class ForecastPoint(BackendOutputModel):
    forecast_at: AwareDatetime | None = None
    hour: int | None = Field(default=None, ge=1, le=3, validation_alias=AliasChoices("hour", "hour_offset"))
    pm25: float | None = Field(default=None, ge=0)
    pm25_min: float | None = Field(default=None, ge=0)
    pm25_max: float | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str = Field(..., min_length=1, max_length=100, validation_alias=AliasChoices("source", "method"))

    @model_validator(mode="after")
    def has_time_and_value(self) -> ForecastPoint:
        if self.forecast_at is None and self.hour is None:
            raise ValueError("forecast point requires forecast_at or hour offset")
        has_point = self.pm25 is not None
        has_range = self.pm25_min is not None and self.pm25_max is not None
        if not has_point and not has_range:
            raise ValueError("forecast point requires pm25 or a complete min/max range")
        if (self.pm25_min is None) != (self.pm25_max is None):
            raise ValueError("forecast range requires both pm25_min and pm25_max")
        if has_range and self.pm25_min > self.pm25_max:
            raise ValueError("forecast pm25_min cannot exceed pm25_max")
        return self


class Pm25Forecast(BackendOutputModel):
    station_id: str
    items: list[ForecastPoint]

    @field_validator("station_id")
    @classmethod
    def station_id_known(cls, value: str) -> str:
        return validate_station_id(value)


class ExtendedForecastHorizon(BackendOutputModel):
    hours_ahead: int = Field(..., ge=1, le=24)
    timestamp: AwareDatetime
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float | None = None


class ExtendedForecast(BackendOutputModel):
    station_id: str
    metric: str
    model: str
    trend_summary: str
    confidence: str
    horizons: list[ExtendedForecastHorizon]


class ExtendedForecastInput(StrictModel):
    station_id: str
    hours: int = Field(default=24, ge=1, le=24)
    metric: Literal["pm25", "aqi", "co2", "noise_db", "temperature"] = "pm25"

    @field_validator("station_id")
    @classmethod
    def check_station(cls, value: str) -> str:
        return validate_station_id(value)


class ActiveAlert(BackendOutputModel):
    alert_id: str
    station_id: str
    alert_type: str
    rule_version: str | None = Field(default=None, min_length=1, max_length=100)
    severity: str
    observed_value: float | None = Field(default=None, ge=0)
    threshold_value: float | None = Field(default=None, ge=0)
    status: Literal["active"]
    created_at: AwareDatetime
    source: str = Field(..., min_length=1, max_length=100)
    title: str | None = None
    description: str | None = None
    unit: str | None = Field(default=None, max_length=20)
    recommendation: str | None = Field(default=None, max_length=500)

    @field_validator("station_id")
    @classmethod
    def station_id_known(cls, value: str) -> str:
        return validate_station_id(value)


class ActiveAlerts(BackendOutputModel):
    items: list[ActiveAlert]


class UserProfile(BackendOutputModel):
    user_id: str
    group: Literal["normal", "sensitive", "outdoor_sport"] = Field(
        validation_alias=AliasChoices("group", "user_group")
    )
    display_name: str | None = None
    source: str | None = None


class WarningProposal(BackendOutputModel):
    proposal_id: str = Field(validation_alias=AliasChoices("proposal_id", "request_id"))
    status: Literal["pending"]
    request_id: str | None = None
    audit_id: str | None = None


class ToolSpec(StrictModel):
    name: ToolName
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    method: Literal["GET", "POST"]
    endpoint: str
    mutating: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SpatialAirQualityInput(StrictModel):
    metric: Literal["aqi", "pm25", "co2", "noise_db", "temperature"] = "aqi"
    forecast_hour: int = Field(default=0, ge=0, le=24)


class SpatialGridPoint(StrictModel):
    lat: FiniteFloat = Field(ge=-90, le=90)
    lon: FiniteFloat = Field(ge=-180, le=180)
    value: FiniteFloat
    intensity: FiniteFloat = Field(ge=0, le=1)
    level: Literal[
        "good",
        "moderate",
        "unhealthy_sensitive",
        "unhealthy",
        "very_unhealthy",
        "hazardous",
    ]


class SpatialWeather(StrictModel):
    wind_speed_ms: FiniteFloat = Field(ge=0, le=60)
    wind_direction_deg: int = Field(ge=0, lt=360)
    source: str = Field(min_length=1)
    observed_at: AwareDatetime
    is_fallback: bool
    is_stale: Literal[False]
    assumptions: list[str] = Field(default_factory=list)


class SpatialDataQuality(StrictModel):
    status: Literal["valid"]
    stations_required: int = Field(ge=3)
    stations_used: list[str] = Field(min_length=3)
    stations_excluded: list[str] = Field(default_factory=list)
    exclusion_reasons: dict[str, list[str]] = Field(default_factory=dict)
    station_sources: list[str] = Field(min_length=1)
    forecast_sources: list[str] = Field(default_factory=list)


class SpatialModel(StrictModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    grid_rows: int = Field(ge=1)
    grid_columns: int = Field(ge=1)
    power: FiniteFloat = Field(gt=0)
    minimum_stations: int = Field(ge=3)


class SpatialExtent(StrictModel):
    south: FiniteFloat = Field(ge=-90, le=90)
    west: FiniteFloat = Field(ge=-180, le=180)
    north: FiniteFloat = Field(ge=-90, le=90)
    east: FiniteFloat = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def ordered_bounds(self) -> SpatialExtent:
        if self.south >= self.north or self.west >= self.east:
            raise ValueError("spatial extent bounds must be ordered")
        return self


class SpatialStationInput(StrictModel):
    station_id: str
    lat: FiniteFloat = Field(ge=-90, le=90)
    lon: FiniteFloat = Field(ge=-180, le=180)
    value: FiniteFloat
    source: str = Field(min_length=1)
    observed_at: AwareDatetime
    forecast_source: str | None = None

    @field_validator("station_id")
    @classmethod
    def station_id_known(cls, value: str) -> str:
        return validate_station_id(value)


class SpatialAirQuality(BackendOutputModel):
    metric: Literal["aqi", "pm25", "co2", "noise_db", "temperature"]
    unit: str = Field(min_length=1)
    timestamp: AwareDatetime
    generated_at: AwareDatetime
    forecast_hour: int = Field(ge=0, le=24)
    source: Literal["spatial_idw_dispersion_model"]
    model_version: str = Field(min_length=1)
    model: SpatialModel
    extent: SpatialExtent
    weather: SpatialWeather
    data_quality: SpatialDataQuality
    station_inputs: list[SpatialStationInput] = Field(min_length=3)
    wind_speed_ms: FiniteFloat = Field(ge=0, le=60)
    wind_direction_deg: int = Field(ge=0, lt=360)
    grid_points: list[SpatialGridPoint] = Field(min_length=1)
    disclaimer: str = Field(min_length=20)


TOOL_REGISTRY: dict[ToolName, ToolSpec] = {
    ToolName.GET_CURRENT_PM25: ToolSpec(
        name=ToolName.GET_CURRENT_PM25,
        description="Fetch the latest valid environmental snapshot for one AirGuard station, with AQI as the primary index and PM2.5 as supporting evidence.",
        input_schema=CurrentPm25Input,
        output_schema=StationMeasurement,
        method="GET",
        endpoint="/api/v1/stations/{station_id}/current",
    ),
    ToolName.GET_STATION_HISTORY: ToolSpec(
        name=ToolName.GET_STATION_HISTORY,
        description="Fetch PM2.5 history for one station over 1 to 72 hours.",
        input_schema=StationHistoryInput,
        output_schema=StationHistory,
        method="GET",
        endpoint="/api/v1/stations/{station_id}/history?hours={hours}",
    ),
    ToolName.COMPARE_STATIONS: ToolSpec(
        name=ToolName.COMPARE_STATIONS,
        description="Fetch current PM2.5 for 2 to 5 stations and return comparable records.",
        input_schema=CompareStationsInput,
        output_schema=StationComparison,
        method="GET",
        endpoint="/api/v1/stations/{station_id}/current",
    ),
    ToolName.GET_WEATHER_CONTEXT: ToolSpec(
        name=ToolName.GET_WEATHER_CONTEXT,
        description="Fetch current weather context for the VinUni/Ocean Park area.",
        input_schema=WeatherContextInput,
        output_schema=WeatherContext,
        method="GET",
        endpoint="/api/v1/weather/current",
    ),
    ToolName.GET_PM25_FORECAST: ToolSpec(
        name=ToolName.GET_PM25_FORECAST,
        description="Fetch a 1 to 3 hour PM2.5 forecast for one station.",
        input_schema=Pm25ForecastInput,
        output_schema=Pm25Forecast,
        method="GET",
        endpoint="/api/v1/stations/{station_id}/forecast",
    ),
    ToolName.GET_EXTENDED_FORECAST: ToolSpec(
        name=ToolName.GET_EXTENDED_FORECAST,
        description="Fetch a 1 to 24 hour multi-step ML time-series forecast for one station with confidence bounds and trend summary.",
        input_schema=ExtendedForecastInput,
        output_schema=ExtendedForecast,
        method="GET",
        endpoint="/api/v1/stations/{station_id}/forecast?model=prophet&hours={hours}",
    ),
    ToolName.GET_ACTIVE_ALERTS: ToolSpec(
        name=ToolName.GET_ACTIVE_ALERTS,
        description="Fetch active deterministic AQI/environmental alerts, optionally filtered by station.",
        input_schema=ActiveAlertsInput,
        output_schema=ActiveAlerts,
        method="GET",
        endpoint="/api/v1/alerts",
    ),
    ToolName.GET_USER_PROFILE: ToolSpec(
        name=ToolName.GET_USER_PROFILE,
        description="Fetch the user's AirGuard profile group for recommendation policy.",
        input_schema=UserProfileInput,
        output_schema=UserProfile,
        method="GET",
        endpoint="/api/v1/users/{user_id}/profile",
    ),
    ToolName.CREATE_WARNING_PROPOSAL: ToolSpec(
        name=ToolName.CREATE_WARNING_PROPOSAL,
        description="Create a pending warning proposal for manager HITL review.",
        input_schema=WarningProposalInput,
        output_schema=WarningProposal,
        method="POST",
        endpoint="/api/v1/proposals",
        mutating=True,
    ),
    ToolName.GET_SPATIAL_AIR_QUALITY: ToolSpec(
        name=ToolName.GET_SPATIAL_AIR_QUALITY,
        description=(
            "Fetch a current or 1-to-24-hour backend-grounded spatial IDW environmental grid, "
            "including wind provenance and station data-quality evidence across Ocean Park 1."
        ),
        input_schema=SpatialAirQualityInput,
        output_schema=SpatialAirQuality,
        method="GET",
        endpoint="/api/v1/spatial/heatmap?metric={metric}&forecast_hour={forecast_hour}",
    ),
}
