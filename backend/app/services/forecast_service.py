from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from math import sqrt
from typing import Any

MIN_HISTORY_POINTS = 3
MODEL_NAME = "damped_linear_trend_v1"
FORECAST_SOURCE = "simulator_history_damped_linear_v1"


class InsufficientForecastHistory(ValueError):  # noqa: N818 - public API compatibility
    """Raised when a forecast would have to invent a trend."""


def trend_forecast(
    history: Sequence[Mapping[str, Any]],
    hours: int,
    *,
    metric: str = "pm25",
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Forecast a selected metric from recent valid simulator history."""
    if not 1 <= hours <= 3:
        raise ValueError("hours must be between 1 and 3")

    points = _normalise_history(history, metric)
    if len(points) < MIN_HISTORY_POINTS:
        raise InsufficientForecastHistory(
            f"at least {MIN_HISTORY_POINTS} valid recent measurements are required"
        )

    points = points[-24:]
    origin = points[0][0]
    x_values = [(measured_at - origin).total_seconds() / 60 for measured_at, _ in points]
    y_values = [value for _, value in points]
    slope_per_minute, intercept = _least_squares(x_values, y_values)
    current_value = y_values[-1]
    raw_hourly_change = slope_per_minute * 60
    max_hourly_change = max(1.0, current_value * 0.25)
    capped_hourly_change = max(-max_hourly_change, min(raw_hourly_change, max_hourly_change))
    damped_hourly_change = capped_hourly_change * 0.65
    residual_spread = _residual_spread(x_values, y_values, slope_per_minute, intercept)
    confidence = _confidence(len(points), residual_spread, current_value)
    generated_at = generated_at or datetime.now(UTC)

    items = []
    for hour in range(1, hours + 1):
        prediction = max(0.0, current_value + damped_hourly_change * hour)
        half_range = max(1.0, residual_spread * (1 + 0.35 * hour), prediction * 0.08)
        item = {
            "hour_offset": hour,
            "forecast_at": (generated_at + timedelta(hours=hour)).isoformat(),
            "value": round(prediction, 2),
            "value_min": round(max(0.0, prediction - half_range), 2),
            "value_max": round(prediction + half_range, 2),
            "confidence": confidence,
            "source": FORECAST_SOURCE,
            "method": MODEL_NAME,
        }
        # Existing PM2.5 clients retain their original response fields.
        if metric == "pm25":
            item.update({"pm25": item["value"], "pm25_min": item["value_min"], "pm25_max": item["value_max"]})
        items.append(item)

    return {
        "items": items,
        "metric": metric,
        "model_name": MODEL_NAME,
        "source": FORECAST_SOURCE,
        "confidence": confidence,
        "history_points": len(points),
        "trend_per_hour": round(damped_hourly_change, 2),
        "trend_pm25_per_hour": round(damped_hourly_change, 2) if metric == "pm25" else None,
        "generated_at": generated_at.isoformat(),
        "freshness": "fresh",
        "limitations": [
            "Dự báo xu hướng ngắn hạn từ dữ liệu simulator, không phải quan trắc chính thức.",
            "Không sử dụng cho quyết định y tế hoặc pháp lý.",
        ],
    }


def _normalise_history(history: Sequence[Mapping[str, Any]], metric: str) -> list[tuple[datetime, float]]:
    points: list[tuple[datetime, float]] = []
    for item in history:
        measured_at = item.get("measured_at")
        value = item.get(metric)
        if measured_at is None or value is None:
            continue
        if isinstance(measured_at, str):
            measured_at = datetime.fromisoformat(measured_at.replace("Z", "+00:00"))
        if measured_at.tzinfo is None:
            continue
        points.append((measured_at.astimezone(UTC), float(value)))
    return sorted(points, key=lambda point: point[0])


def _least_squares(x_values: list[float], y_values: list[float]) -> tuple[float, float]:
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)
    denominator = sum((value - mean_x) ** 2 for value in x_values)
    if denominator == 0:
        raise InsufficientForecastHistory("measurements need distinct timestamps")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values)) / denominator
    return slope, mean_y - slope * mean_x


def _residual_spread(x_values: list[float], y_values: list[float], slope: float, intercept: float) -> float:
    residuals = [y - (slope * x + intercept) for x, y in zip(x_values, y_values)]
    return sqrt(sum(value * value for value in residuals) / len(residuals))


def _confidence(point_count: int, residual_spread: float, current_value: float) -> float:
    sample_score = min(0.82, 0.42 + point_count * 0.025)
    variability_penalty = min(0.25, residual_spread / max(current_value, 10.0) * 0.35)
    return round(max(0.35, sample_score - variability_penalty), 2)
