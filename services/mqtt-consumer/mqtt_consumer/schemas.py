from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _require_timezone(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("timestamp must include timezone")
    return value


class MeasurementPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1, max_length=100)
    station_id: str = Field(pattern=r"^S[0-9]{2}$")
    pm25: float = Field(ge=0, le=500)
    co2: float | None = Field(default=None, ge=250, le=10000)
    noise_db: float | None = Field(default=None, ge=20, le=140)
    temperature: float | None = Field(default=None, ge=-20, le=60)
    humidity: float | None = Field(default=None, ge=0, le=100)
    wind_speed: float | None = Field(default=None, ge=0, le=60)
    wind_direction: float | None = Field(default=None, ge=0, le=360)
    rainfall: float | None = Field(default=None, ge=0, le=500)
    timestamp: datetime
    source: Literal["simulator"]

    @field_validator("timestamp")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        return _require_timezone(value)


class StationStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str = Field(pattern=r"^S[0-9]{2}$")
    status: Literal["online", "offline"]
    timestamp: datetime
    source: Literal["simulator"]
    reason: str | None = Field(default=None, max_length=200)

    @field_validator("timestamp")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        return _require_timezone(value)


class DeviceStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(min_length=1, max_length=100)
    device_id: str = Field(min_length=1, max_length=50)
    status: Literal["succeeded", "rejected", "failed", "duplicate"]
    timestamp: datetime
    is_simulated: Literal[True]
    device_state: Literal["RUNNING_BOOST", "AIR_PURIFIER_ON", "ECO_MODE"] | None = None
    reason: str | None = Field(default=None, max_length=200)

    @field_validator("timestamp")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        return _require_timezone(value)
