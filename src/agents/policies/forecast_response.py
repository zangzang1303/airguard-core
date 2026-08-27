from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Any


@dataclass(frozen=True)
class ForecastAssessment:
    station_id: str
    trend: str
    confidence: float | None
    confidence_label: str
    generated_at: str | None
    model_name: str | None
    freshness: str | None
    limitations: tuple[str, ...]


def forecast_value(point: dict[str, Any]) -> float | None:
    if point.get("value") is not None:
        return float(point["value"])
    if point.get("value_min") is not None and point.get("value_max") is not None:
        return (float(point["value_min"]) + float(point["value_max"])) / 2
    # Legacy direct-policy callers may still supply PM2.5 aliases; tool output
    # itself is canonicalized by ForecastPoint before reaching the composer.
    if point.get("pm25") is not None:
        return float(point["pm25"])
    if point.get("pm25_min") is not None and point.get("pm25_max") is not None:
        return (float(point["pm25_min"]) + float(point["pm25_max"])) / 2
    return None


def assess_forecast(
    forecast: dict[str, Any],
    *,
    current: dict[str, Any] | None = None,
) -> ForecastAssessment:
    items = forecast.get("items", [])
    if not items:
        raise ValueError("forecast requires at least one point")

    station_id = str(forecast.get("station_id") or "")
    if not station_id:
        raise ValueError("forecast requires station_id")
    if current and current.get("station_id") != station_id:
        raise ValueError("current and forecast station_id must match")

    values = [value for item in items if (value := forecast_value(item)) is not None]
    if not values:
        raise ValueError("forecast requires canonical values")

    confidences = [float(item["confidence"]) for item in items if item.get("confidence") is not None]
    confidence = fmean(confidences) if confidences else _top_level_confidence(forecast.get("confidence"))
    confidence_label = _confidence_label(confidence, forecast.get("confidence"))

    reference = float(current["pm25"]) if current and current.get("pm25") is not None else values[0]
    delta = values[-1] - reference
    tolerance = max(2.0, abs(reference) * 0.05)
    if confidence is not None and confidence < 0.5:
        trend = "uncertain"
    elif delta > tolerance:
        trend = "increasing"
    elif delta < -tolerance:
        trend = "decreasing"
    else:
        trend = "stable"

    generated_at = _optional_text(forecast.get("generated_at"))
    model_name = _optional_text(forecast.get("model_name") or forecast.get("model_version"))
    freshness = _optional_text(forecast.get("freshness"))
    limitations: list[str] = []
    if generated_at is None:
        limitations.append("backend chưa cung cấp thời điểm tạo dự báo")
    if model_name is None:
        limitations.append("backend chưa cung cấp tên hoặc phiên bản mô hình")
    if freshness is None:
        limitations.append("backend chưa cung cấp freshness tổng thể của dự báo")
    elif freshness.lower() not in {"fresh", "valid"}:
        limitations.append(f"freshness dự báo là {freshness}")
    if confidence is None:
        limitations.append("backend chưa cung cấp confidence")
    elif confidence < 0.5:
        limitations.append("confidence thấp; không dùng xu hướng dự báo để khẳng định chắc chắn")

    return ForecastAssessment(
        station_id=station_id,
        trend=trend,
        confidence=confidence,
        confidence_label=confidence_label,
        generated_at=generated_at,
        model_name=model_name,
        freshness=freshness,
        limitations=tuple(limitations),
    )


def forecast_is_fresh(assessment: ForecastAssessment) -> bool:
    return assessment.freshness is not None and assessment.freshness.lower() == "fresh"


def _top_level_confidence(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    mapping = {"low": 0.3, "medium": 0.6, "high": 0.9}
    return mapping.get(str(value).lower()) if value is not None else None


def _confidence_label(confidence: float | None, raw: Any) -> str:
    if confidence is None:
        return str(raw) if raw is not None else "unknown"
    if confidence < 0.5:
        return "low"
    if confidence < 0.8:
        return "medium"
    return "high"


def _optional_text(value: Any) -> str | None:
    return str(value) if value not in (None, "") else None
