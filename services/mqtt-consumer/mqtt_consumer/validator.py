from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Generic, TypeVar

from pydantic import ValidationError

from .schemas import DeviceStatusPayload, MeasurementPayload, StationStatusPayload
from .station_catalog import StationCatalog

MEASUREMENT_TOPIC_RE = re.compile(r"^airguard/stations/(?P<station_id>S[0-9]{2})/measurements$")
STATUS_TOPIC_RE = re.compile(r"^airguard/stations/(?P<station_id>S[0-9]{2})/status$")
DEVICE_STATUS_TOPIC_RE = re.compile(r"^airguard/devices/(?P<device_id>[A-Za-z0-9_.-]+)/status$")
PayloadT = TypeVar("PayloadT")


class ValidationErrorCode(StrEnum):
    MALFORMED = "malformed"
    UNKNOWN_TOPIC = "unknown_topic"
    TOPIC_STATION_MISMATCH = "topic_station_mismatch"
    UNKNOWN_STATION = "unknown_station"
    UNKNOWN_DEVICE = "unknown_device"
    RANGE_ERROR = "range_error"
    FUTURE_TIME = "future_time"
    STALE = "stale"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class ValidationResult(Generic[PayloadT]):
    accepted: bool
    payload: PayloadT | None = None
    reason: ValidationErrorCode | None = None
    detail: str | None = None


def _decode_json(raw_payload: bytes | str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if isinstance(raw_payload, bytes):
            raw_payload = raw_payload.decode("utf-8")
        decoded = json.loads(raw_payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(decoded, dict):
        return None, "payload must be a JSON object"
    return decoded, None


def _validate_time(
    event_time: datetime,
    now: datetime,
    stale_after_seconds: int,
    max_future_skew_seconds: int,
) -> ValidationResult[Any] | None:
    event_utc = event_time.astimezone(timezone.utc)
    now_utc = now.astimezone(timezone.utc)
    age_seconds = (now_utc - event_utc).total_seconds()
    if age_seconds < -max_future_skew_seconds:
        return ValidationResult(False, reason=ValidationErrorCode.FUTURE_TIME, detail="timestamp is too far in the future")
    if age_seconds > stale_after_seconds:
        return ValidationResult(False, reason=ValidationErrorCode.STALE, detail="timestamp is older than stale threshold")
    return None


def validate_measurement_message(
    topic: str,
    raw_payload: bytes | str,
    catalog: StationCatalog,
    *,
    now: datetime | None = None,
    stale_after_seconds: int = 300,
    max_future_skew_seconds: int = 60,
) -> ValidationResult[MeasurementPayload]:
    match = MEASUREMENT_TOPIC_RE.match(topic)
    if not match:
        return ValidationResult(False, reason=ValidationErrorCode.UNKNOWN_TOPIC, detail="unexpected measurement topic")

    decoded, decode_error = _decode_json(raw_payload)
    if decoded is None:
        return ValidationResult(False, reason=ValidationErrorCode.MALFORMED, detail=decode_error)

    try:
        payload = MeasurementPayload.model_validate(decoded)
    except ValidationError as exc:
        return ValidationResult(False, reason=ValidationErrorCode.RANGE_ERROR, detail=exc.errors()[0]["msg"])

    topic_station = match.group("station_id")
    if payload.station_id != topic_station:
        return ValidationResult(False, reason=ValidationErrorCode.TOPIC_STATION_MISMATCH, detail="station_id differs from topic")
    if not catalog.has_station(payload.station_id):
        return ValidationResult(False, reason=ValidationErrorCode.UNKNOWN_STATION, detail="station is not in master data")

    time_error = _validate_time(
        payload.timestamp,
        now or datetime.now(timezone.utc),
        stale_after_seconds,
        max_future_skew_seconds,
    )
    if time_error:
        return ValidationResult(False, reason=time_error.reason, detail=time_error.detail)

    return ValidationResult(True, payload=payload)


def validate_status_message(
    topic: str,
    raw_payload: bytes | str,
    catalog: StationCatalog,
    *,
    now: datetime | None = None,
    stale_after_seconds: int = 300,
    max_future_skew_seconds: int = 60,
) -> ValidationResult[StationStatusPayload]:
    match = STATUS_TOPIC_RE.match(topic)
    if not match:
        return ValidationResult(False, reason=ValidationErrorCode.UNKNOWN_TOPIC, detail="unexpected status topic")

    decoded, decode_error = _decode_json(raw_payload)
    if decoded is None:
        return ValidationResult(False, reason=ValidationErrorCode.MALFORMED, detail=decode_error)

    try:
        payload = StationStatusPayload.model_validate(decoded)
    except ValidationError as exc:
        return ValidationResult(False, reason=ValidationErrorCode.RANGE_ERROR, detail=exc.errors()[0]["msg"])

    topic_station = match.group("station_id")
    if payload.station_id != topic_station:
        return ValidationResult(False, reason=ValidationErrorCode.TOPIC_STATION_MISMATCH, detail="station_id differs from topic")
    if not catalog.has_station(payload.station_id):
        return ValidationResult(False, reason=ValidationErrorCode.UNKNOWN_STATION, detail="station is not in master data")

    time_error = _validate_time(
        payload.timestamp,
        now or datetime.now(timezone.utc),
        stale_after_seconds,
        max_future_skew_seconds,
    )
    if time_error:
        return ValidationResult(False, reason=time_error.reason, detail=time_error.detail)

    return ValidationResult(True, payload=payload)


def validate_device_status_message(
    topic: str,
    raw_payload: bytes | str,
) -> ValidationResult[DeviceStatusPayload]:
    match = DEVICE_STATUS_TOPIC_RE.match(topic)
    if not match:
        return ValidationResult(False, reason=ValidationErrorCode.UNKNOWN_TOPIC, detail="unexpected device status topic")
    decoded, decode_error = _decode_json(raw_payload)
    if decoded is None:
        return ValidationResult(False, reason=ValidationErrorCode.MALFORMED, detail=decode_error)
    try:
        payload = DeviceStatusPayload.model_validate(decoded)
    except Exception as exc:
        return ValidationResult(False, reason=ValidationErrorCode.RANGE_ERROR, detail=str(exc))
    if payload.device_id != match.group("device_id"):
        return ValidationResult(False, reason=ValidationErrorCode.TOPIC_STATION_MISMATCH, detail="device_id differs from topic")
    return ValidationResult(True, payload=payload)


