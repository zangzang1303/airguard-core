from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from .air_quality import pm25_aqi


class ProphetForecastService:
    """Extended additive time-series forecast used by the 0-24h map timeline.

    The class name is retained for import compatibility with the earlier backlog.
    The implementation is a dependency-free additive Fourier regression, not the
    third-party Prophet package and not a trained official forecasting model.
    """

    MODEL_NAME = "extended_additive_fourier_v3"
    SOURCE = "simulator_history_additive_fourier_v3"
    TRAFFIC_STATIONS = frozenset({"S01", "S05"})
    METRIC_RANGES = {
        "pm25": (0.0, 500.0),
        "aqi": (0.0, 500.0),
        "co2": (300.0, 5000.0),
        "noise_db": (20.0, 120.0),
        "temperature": (-10.0, 50.0),
    }

    def forecast(
        self,
        station_id: str,
        history: list[dict[str, Any]],
        hours: int = 24,
        metric: Literal["pm25", "aqi", "co2", "noise_db", "temperature"] = "pm25",
        *,
        generated_at: datetime | None = None,
    ) -> dict[str, Any]:
        if isinstance(hours, bool) or not 1 <= hours <= 24:
            raise ValueError("hours must be between 1 and 24")
        metric = metric.lower()
        if metric not in self.METRIC_RANGES:
            raise ValueError(f"unsupported forecast metric: {metric}")

        # AQI remains the documented PM2.5 concentration sub-index. Forecasting
        # PM2.5 first avoids treating AQI as an unrelated measured pollutant.
        if metric == "aqi":
            pm25_result = self.forecast(
                station_id,
                history,
                hours,
                "pm25",
                generated_at=generated_at,
            )
            return self._as_aqi(pm25_result)

        extracted = self._extract_history(history, metric)
        if len(extracted) < 3:
            raise ValueError("at least three timestamped measurements are required for forecasting")

        origin = extracted[0][0]
        forecast_origin = extracted[-1][0]
        generated_at = self._aware_utc(generated_at or datetime.now(UTC))
        weather_by_hour = self._weather_climatology(history)

        adjusted_values = []
        for measured_at, value in extracted:
            weather = self._weather_for_hour(weather_by_hour, measured_at, history)
            adjusted_values.append(
                value
                - self._traffic_modifier(station_id, measured_at, metric)
                - self._inversion_modifier(measured_at, weather, metric)
            )

        design = [self._features(measured_at, origin) for measured_at, _ in extracted]
        coefficients = self._ridge_least_squares(design, adjusted_values)
        fitted = [self._dot(row, coefficients) for row in design]
        residuals = [actual - estimate for actual, estimate in zip(adjusted_values, fitted)]
        sigma_residual = max(0.5, math.sqrt(sum(value * value for value in residuals) / len(residuals)))
        anchor_error = residuals[-1]
        min_value, max_value = self.METRIC_RANGES[metric]

        horizons: list[dict[str, Any]] = []
        previous_weather = self._weather_for_hour(weather_by_hour, forecast_origin, history)
        for hour in range(1, hours + 1):
            forecast_at = forecast_origin + timedelta(hours=hour)
            weather = self._weather_for_hour(weather_by_hour, forecast_at, history)
            weather["temperature_drop_c"] = round(
                float(weather["temperature"]) - float(previous_weather["temperature"]), 2
            )
            traffic_effect = self._traffic_modifier(station_id, forecast_at, metric)
            inversion_effect = self._inversion_modifier(forecast_at, weather, metric)
            estimate = self._dot(self._features(forecast_at, origin), coefficients)
            # Preserve recent local information without allowing a transient spike
            # to dominate the whole day.
            estimate += anchor_error * math.exp(-hour / 6.0)
            estimate += traffic_effect + inversion_effect
            predicted = round(max(min_value, min(max_value, estimate)), 1)

            uncertainty = 1.645 * sigma_residual * math.sqrt(1.0 + 0.14 * hour)
            lower = round(max(min_value, predicted - uncertainty), 1)
            upper = round(min(max_value, predicted + uncertainty), 1)
            confidence = round(
                max(0.35, min(0.95, 0.93 - hour * 0.016 - sigma_residual * 0.004)),
                2,
            )
            horizons.append(
                {
                    "hours_ahead": hour,
                    "hour_offset": hour,
                    "timestamp": forecast_at.isoformat(),
                    "forecast_at": forecast_at.isoformat(),
                    "predicted_value": predicted,
                    "value": predicted,
                    "lower_bound": lower,
                    "upper_bound": upper,
                    "value_min": lower,
                    "value_max": upper,
                    "pm25": predicted if metric == "pm25" else None,
                    "pm25_min": lower if metric == "pm25" else None,
                    "pm25_max": upper if metric == "pm25" else None,
                    "confidence": confidence,
                    "source": self.SOURCE,
                    "method": self.MODEL_NAME,
                    "weather_context": {
                        "humidity": round(float(weather["humidity"]), 1),
                        "temperature": round(float(weather["temperature"]), 1),
                        "wind_speed": round(float(weather["wind_speed"]), 1),
                        "temperature_drop_c": weather["temperature_drop_c"],
                        "nocturnal_inversion_applied": inversion_effect > 0,
                        "traffic_rush_applied": traffic_effect > 0,
                    },
                }
            )
            previous_weather = weather

        return {
            "station_id": station_id,
            "metric": metric,
            "model": self.MODEL_NAME,
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_NAME,
            "source": self.SOURCE,
            "horizon_hours": hours,
            "generated_at": generated_at.isoformat(),
            "forecast_origin": forecast_origin.isoformat(),
            "timestamp": generated_at.isoformat(),
            "freshness": "fresh",
            "is_stale": False,
            "confidence": round(sum(item["confidence"] for item in horizons) / len(horizons), 2),
            "horizons": horizons,
            "items": horizons,
            "trend_summary": self._generate_trend_summary(metric, horizons),
            "limitations": [
                "Mô hình additive Fourier nhẹ từ dữ liệu simulator; không phải thư viện Prophet hay mô hình quan trắc chính thức.",
                "Tác động nghịch nhiệt và giao thông là giả định demo có phiên bản, không dùng cho quyết định y tế hoặc pháp lý.",
            ],
        }

    def golden_windows(
        self,
        forecast: dict[str, Any],
        *,
        minimum_wind_speed: float = 2.0,
        minimum_duration_hours: int = 2,
    ) -> dict[str, Any]:
        """Extract contiguous AQI-safe windows and the maximum forecast point."""
        if forecast.get("metric") != "aqi":
            raise ValueError("golden windows require an AQI forecast")
        items = list(forecast.get("items") or forecast.get("horizons") or [])
        if not items:
            raise ValueError("forecast contains no hourly points")

        eligible = []
        for item in items:
            weather = item.get("weather_context") or {}
            wind = weather.get("wind_speed")
            value = item.get("value", item.get("predicted_value"))
            eligible.append(
                value is not None
                and float(value) <= 50
                and wind is not None
                and float(wind) >= minimum_wind_speed
            )

        windows: list[dict[str, Any]] = []
        start = 0
        while start < len(items):
            if not eligible[start]:
                start += 1
                continue
            end = start
            while end + 1 < len(items) and eligible[end + 1]:
                end += 1
            duration = end - start + 1
            if duration >= minimum_duration_hours:
                segment = items[start : end + 1]
                windows.append(
                    {
                        "start_at": segment[0]["forecast_at"],
                        "end_at": (
                            datetime.fromisoformat(segment[-1]["forecast_at"])
                            + timedelta(hours=1)
                        ).isoformat(),
                        "duration_hours": duration,
                        "minimum_aqi": min(float(point["value"]) for point in segment),
                        "average_aqi": round(
                            sum(float(point["value"]) for point in segment) / duration,
                            1,
                        ),
                        "minimum_wind_speed": min(
                            float(point["weather_context"]["wind_speed"])
                            for point in segment
                        ),
                    }
                )
            start = end + 1

        windows.sort(
            key=lambda item: (
                item["average_aqi"],
                -item["minimum_wind_speed"],
                item["start_at"],
            )
        )
        worst = max(
            items,
            key=lambda item: float(item.get("value", item.get("predicted_value", -1))),
        )
        return {
            "station_id": forecast["station_id"],
            "generated_at": forecast["generated_at"],
            "source": forecast["source"],
            "model_name": forecast["model_name"],
            "criteria": {
                "maximum_aqi": 50,
                "minimum_wind_speed": minimum_wind_speed,
                "minimum_duration_hours": minimum_duration_hours,
            },
            "best_window": windows[0] if windows else None,
            "candidate_windows": windows,
            "worst_window": {
                "forecast_at": worst["forecast_at"],
                "aqi": float(worst.get("value", worst.get("predicted_value"))),
                "wind_speed": float(
                    (worst.get("weather_context") or {}).get("wind_speed", 0.0)
                ),
            },
            "limitations": forecast["limitations"],
        }

    @staticmethod
    def _aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        return value.astimezone(UTC)

    def _extract_history(
        self,
        history: list[dict[str, Any]],
        metric: str,
    ) -> list[tuple[datetime, float]]:
        extracted: list[tuple[datetime, float]] = []
        for point in history:
            value = point.get(metric)
            raw_timestamp = point.get("measured_at") or point.get("timestamp")
            if value is None or raw_timestamp is None:
                continue
            try:
                measured_at = (
                    raw_timestamp
                    if isinstance(raw_timestamp, datetime)
                    else datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
                )
                if measured_at.tzinfo is None or measured_at.utcoffset() is None:
                    continue
                numeric = float(value)
                if math.isfinite(numeric):
                    extracted.append((measured_at.astimezone(UTC), numeric))
            except (TypeError, ValueError):
                continue
        return sorted(extracted, key=lambda item: item[0])

    @staticmethod
    def _features(measured_at: datetime, origin: datetime) -> list[float]:
        elapsed_days = (measured_at - origin).total_seconds() / 86_400
        local_hour = (measured_at.astimezone(UTC).hour + 7) + measured_at.minute / 60
        phase_24 = 2 * math.pi * local_hour / 24
        phase_12 = 2 * math.pi * local_hour / 12
        return [
            1.0,
            elapsed_days,
            math.sin(phase_24),
            math.cos(phase_24),
            math.sin(phase_12),
            math.cos(phase_12),
        ]

    @classmethod
    def _traffic_modifier(
        cls,
        station_id: str,
        measured_at: datetime,
        metric: str,
    ) -> float:
        if metric != "pm25" or station_id not in cls.TRAFFIC_STATIONS:
            return 0.0
        local_hour = (measured_at.astimezone(UTC).hour + 7) % 24
        if 7 <= local_hour <= 9:
            return 8.5
        if 17 <= local_hour <= 19:
            return 11.0
        return 0.0

    @staticmethod
    def _inversion_modifier(
        measured_at: datetime,
        weather: dict[str, float],
        metric: str,
    ) -> float:
        if metric != "pm25":
            return 0.0
        local_hour = (measured_at.astimezone(UTC).hour + 7) % 24
        is_night = local_hour >= 22 or local_hour <= 5
        return (
            3.5
            if is_night
            and weather.get("humidity", 0.0) > 80
            and weather.get("temperature_drop_c", -0.1) < 0
            else 0.0
        )

    @staticmethod
    def _weather_climatology(
        history: list[dict[str, Any]],
    ) -> dict[int, dict[str, float]]:
        buckets: dict[int, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        previous_temp: float | None = None
        ordered = sorted(
            history,
            key=lambda item: str(item.get("measured_at") or item.get("timestamp") or ""),
        )
        for point in ordered:
            raw_timestamp = point.get("measured_at") or point.get("timestamp")
            if raw_timestamp is None:
                continue
            try:
                measured_at = (
                    raw_timestamp
                    if isinstance(raw_timestamp, datetime)
                    else datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
                )
                local_hour = (measured_at.astimezone(UTC).hour + 7) % 24
            except (TypeError, ValueError):
                continue
            for key, fallback in (
                ("humidity", 70.0),
                ("temperature", 30.0),
                ("wind_speed", 2.4),
            ):
                try:
                    value = float(point.get(key, fallback))
                    if math.isfinite(value):
                        buckets[local_hour][key].append(value)
                except (TypeError, ValueError):
                    pass
            current_temp = point.get("temperature")
            if current_temp is not None and previous_temp is not None:
                buckets[local_hour]["temperature_drop_c"].append(
                    float(current_temp) - previous_temp
                )
            if current_temp is not None:
                previous_temp = float(current_temp)

        return {
            hour: {
                key: sum(values) / len(values)
                for key, values in fields.items()
                if values
            }
            for hour, fields in buckets.items()
        }

    @staticmethod
    def _weather_for_hour(
        climatology: dict[int, dict[str, float]],
        forecast_at: datetime,
        history: list[dict[str, Any]],
    ) -> dict[str, float]:
        local_hour = (forecast_at.astimezone(UTC).hour + 7) % 24
        latest = history[-1] if history else {}
        bucket = climatology.get(local_hour, {})
        return {
            "humidity": float(
                bucket.get("humidity", latest.get("humidity", 70.0) or 70.0)
            ),
            "temperature": float(
                bucket.get("temperature", latest.get("temperature", 30.0) or 30.0)
            ),
            "wind_speed": float(
                bucket.get("wind_speed", latest.get("wind_speed", 2.4) or 2.4)
            ),
            "temperature_drop_c": float(bucket.get("temperature_drop_c", -0.1)),
        }

    @staticmethod
    def _ridge_least_squares(
        matrix: list[list[float]],
        values: list[float],
    ) -> list[float]:
        size = len(matrix[0])
        normal = [[0.0 for _ in range(size + 1)] for _ in range(size)]
        for row, value in zip(matrix, values):
            for i in range(size):
                normal[i][-1] += row[i] * value
                for j in range(size):
                    normal[i][j] += row[i] * row[j]
        for index in range(1, size):
            normal[index][index] += 1e-4

        for pivot in range(size):
            best = max(range(pivot, size), key=lambda row: abs(normal[row][pivot]))
            normal[pivot], normal[best] = normal[best], normal[pivot]
            divisor = normal[pivot][pivot]
            if abs(divisor) < 1e-10:
                return [sum(values) / len(values)] + [0.0] * (size - 1)
            normal[pivot] = [value / divisor for value in normal[pivot]]
            for row in range(size):
                if row == pivot:
                    continue
                factor = normal[row][pivot]
                normal[row] = [
                    left - factor * right
                    for left, right in zip(normal[row], normal[pivot])
                ]
        return [normal[row][-1] for row in range(size)]

    @staticmethod
    def _dot(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))

    def _as_aqi(self, pm25_result: dict[str, Any]) -> dict[str, Any]:
        items = []
        for point in pm25_result["items"]:
            value = float(pm25_aqi(point["value"]))
            lower = float(pm25_aqi(point["value_min"]))
            upper = float(pm25_aqi(point["value_max"]))
            items.append(
                {
                    **point,
                    "predicted_value": value,
                    "value": value,
                    "lower_bound": min(lower, value),
                    "upper_bound": max(upper, value),
                    "value_min": min(lower, value),
                    "value_max": max(upper, value),
                    "pm25": None,
                    "pm25_min": None,
                    "pm25_max": None,
                }
            )
        return {
            **pm25_result,
            "metric": "aqi",
            "horizons": items,
            "items": items,
            "trend_summary": self._generate_trend_summary("aqi", items),
        }

    @staticmethod
    def _generate_trend_summary(
        metric: str,
        horizons: list[dict[str, Any]],
    ) -> str:
        values = [float(point["value"]) for point in horizons]
        peak = max(horizons, key=lambda point: float(point["value"]))
        best = min(horizons, key=lambda point: float(point["value"]))
        direction = (
            "tăng"
            if values[-1] > values[0] + 4
            else "giảm"
            if values[-1] < values[0] - 4
            else "ổn định"
        )
        label = (
            "AQI"
            if metric == "aqi"
            else "PM2.5"
            if metric == "pm25"
            else metric.upper()
        )
        return (
            f"{label} dự báo {direction} trong {len(horizons)} giờ tới; "
            f"thấp nhất {best['value']} tại {best['forecast_at']} và cao nhất "
            f"{peak['value']} tại {peak['forecast_at']}. Kết quả dùng dữ liệu "
            "simulator và chỉ có giá trị tham khảo cho demo."
        )


prophet_service = ProphetForecastService()
