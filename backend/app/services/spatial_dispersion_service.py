from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from .air_quality import pm25_aqi
from .database import ServiceError
from .prophet_forecast_service import ProphetForecastService
from .station_service import StationService
from .weather_service import WeatherService


class WeatherProvider(Protocol):
    def current_weather(self) -> dict[str, object]: ...


class ForecastProvider(Protocol):
    def forecast(
        self,
        station_id: str,
        history: list[dict[str, Any]],
        hours: int,
        metric: str,
    ) -> dict[str, Any]: ...


class SpatialDispersionService:
    """Wind-adjusted IDW interpolation clipped to the Ocean Park 1 polygon.

    Current grids use only fresh, valid, online station snapshots. Future grids
    use the backend forecast engine and exclude stations without enough history.
    """

    BOUNDARY_POLYGON: list[tuple[float, float]] = [
        (21.0047847, 105.9477604),
        (20.9933962, 105.9628773),
        (20.9890436, 105.9600712),
        (20.9852230, 105.9518985),
        (20.9840728, 105.9509930),
        (20.9851752, 105.9432602),
        (20.9921545, 105.9371584),
        (20.9968500, 105.9334673),
        (20.9980664, 105.9352872),
        (21.0017814, 105.9420739),
    ]

    LAT_MIN = 20.9840
    LAT_MAX = 21.0050
    LON_MIN = 105.9330
    LON_MAX = 105.9630
    GRID_ROWS = 30
    GRID_COLS = 30
    IDW_POWER = 2.0
    IDW_EPSILON_KM = 0.0001
    MIN_STATIONS = 3
    MIN_FORECAST_POINTS = 3
    DEFAULT_WIND_DIRECTION_DEG = 135
    MODEL_NAME = "wind_adjusted_inverse_distance_weighting"
    MODEL_VERSION = "idw-dispersion-v2.0"
    SOURCE = "spatial_idw_dispersion_model"

    METRIC_ALIASES = {"noise": "noise_db"}
    METRIC_UNITS = {
        "aqi": "AQI",
        "pm25": "µg/m³",
        "co2": "ppm",
        "noise_db": "dB",
        "temperature": "°C",
    }
    METRIC_RANGES = {
        "aqi": (0.0, 500.0),
        "pm25": (0.0, 500.0),
        "co2": (250.0, 10_000.0),
        "noise_db": (20.0, 140.0),
        "temperature": (-20.0, 60.0),
    }

    def __init__(
        self,
        station_service: StationService,
        *,
        weather_provider: WeatherProvider | None = None,
        forecast_provider: ForecastProvider | None = None,
    ) -> None:
        self.station_service = station_service
        self.weather_provider = weather_provider or WeatherService()
        self.forecast_provider = forecast_provider or ProphetForecastService()

    @classmethod
    def _is_inside_boundary(cls, lat: float, lon: float) -> bool:
        """Return whether a point is inside the configured polygon using ray casting."""
        polygon = cls.BOUNDARY_POLYGON
        inside = False
        previous_lat, previous_lon = polygon[0]
        for index in range(1, len(polygon) + 1):
            current_lat, current_lon = polygon[index % len(polygon)]
            if min(previous_lat, current_lat) < lat <= max(previous_lat, current_lat):
                if lon <= max(previous_lon, current_lon):
                    intersection_lon = previous_lon
                    if previous_lat != current_lat:
                        intersection_lon = (
                            (lat - previous_lat)
                            * (current_lon - previous_lon)
                            / (current_lat - previous_lat)
                            + previous_lon
                        )
                    if previous_lon == current_lon or lon <= intersection_lon:
                        inside = not inside
            previous_lat, previous_lon = current_lat, current_lon
        return inside

    def calculate_heatmap(
        self,
        metric: str = "aqi",
        forecast_hour: int = 0,
    ) -> dict[str, Any]:
        metric = self._normalise_metric(metric)
        self._validate_forecast_hour(forecast_hour)

        generated_at = datetime.now(UTC)
        weather = self._weather_context(forecast_hour)
        station_inputs, excluded = self._station_inputs(metric, forecast_hour)
        self._require_spatial_coverage(station_inputs, excluded, metric, forecast_hour)

        wind_speed_ms = float(weather["wind_speed_ms"])
        wind_direction_deg = int(weather["wind_direction_deg"])
        grid_points = self._build_grid(
            station_inputs,
            metric=metric,
            wind_speed_ms=wind_speed_ms,
            wind_direction_deg=wind_direction_deg,
        )
        valid_at = generated_at + timedelta(hours=forecast_hour)
        station_sources = sorted({str(item["source"]) for item in station_inputs})
        forecast_sources = sorted(
            {
                str(item["forecast_source"])
                for item in station_inputs
                if item.get("forecast_source")
            }
        )

        return {
            "metric": metric,
            "unit": self.METRIC_UNITS[metric],
            "timestamp": valid_at.isoformat(),
            "generated_at": generated_at.isoformat(),
            "forecast_hour": forecast_hour,
            "source": self.SOURCE,
            "model_version": self.MODEL_VERSION,
            "model": {
                "name": self.MODEL_NAME,
                "version": self.MODEL_VERSION,
                "grid_rows": self.GRID_ROWS,
                "grid_columns": self.GRID_COLS,
                "power": self.IDW_POWER,
                "minimum_stations": self.MIN_STATIONS,
            },
            "weather": weather,
            "wind_speed_ms": wind_speed_ms,
            "wind_direction_deg": wind_direction_deg,
            "extent": {
                "south": self.LAT_MIN,
                "west": self.LON_MIN,
                "north": self.LAT_MAX,
                "east": self.LON_MAX,
            },
            "data_quality": {
                "status": "valid",
                "stations_required": self.MIN_STATIONS,
                "stations_used": [item["station_id"] for item in station_inputs],
                "stations_excluded": sorted(excluded),
                "exclusion_reasons": excluded,
                "station_sources": station_sources,
                "forecast_sources": forecast_sources,
            },
            "station_inputs": station_inputs,
            "grid_points": grid_points,
            "disclaimer": (
                "Mô hình nội suy trực quan IDW có hiệu chỉnh gió từ dữ liệu simulator/fallback; "
                "không phải mô hình lan truyền vật lý hoặc quan trắc chính thức."
            ),
        }

    def _station_inputs(
        self,
        metric: str,
        forecast_hour: int,
    ) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
        try:
            stations = self.station_service.list_stations(allow_fallback=False)
        except ServiceError as exc:
            if exc.code != "station_data_unavailable":
                raise
            raise ServiceError(
                "spatial_station_data_unavailable",
                "Station snapshots are unavailable for spatial interpolation",
                503,
                {"upstream_code": exc.code},
            ) from exc
        except Exception as exc:
            raise ServiceError(
                "spatial_station_data_unavailable",
                "Station snapshots are unavailable for spatial interpolation",
                503,
            ) from exc

        included: list[dict[str, Any]] = []
        excluded: dict[str, list[str]] = {}
        for index, station in enumerate(stations):
            station_id = str(station.get("station_id") or f"unknown-{index}")
            reasons = self._station_exclusion_reasons(station, metric)
            if reasons:
                excluded[station_id] = reasons
                continue

            value = self._extract_metric_value(station, metric)
            forecast_source: str | None = None
            observed_at = station.get("updated_at") or station.get("timestamp")
            if forecast_hour > 0:
                try:
                    value, forecast_source, observed_at = self._forecast_value(
                        station_id,
                        metric,
                        forecast_hour,
                    )
                except (ServiceError, TypeError, ValueError, KeyError) as exc:
                    excluded[station_id] = [
                        exc.code if isinstance(exc, ServiceError) else "invalid_forecast"
                    ]
                    continue

            included.append(
                {
                    "station_id": station_id,
                    "lat": float(station["latitude"]),
                    "lon": float(station["longitude"]),
                    "value": value,
                    "source": str(station["source"]),
                    "observed_at": self._iso_or_none(observed_at),
                    "forecast_source": forecast_source,
                }
            )
        return included, excluded

    def _station_exclusion_reasons(self, station: dict[str, Any], metric: str) -> list[str]:
        reasons: list[str] = []
        if station.get("active") is False:
            reasons.append("inactive")
        if station.get("status") != "online":
            reasons.append("not_online")
        if station.get("is_stale") is not False:
            reasons.append("stale_or_unknown_freshness")
        if station.get("freshness") not in {None, "fresh"}:
            reasons.append("not_fresh")
        if station.get("quality_flag") not in {None, "valid"}:
            reasons.append("invalid_quality")
        if not station.get("source"):
            reasons.append("missing_source")
        if self._aware_datetime(station.get("updated_at") or station.get("timestamp")) is None:
            reasons.append("missing_or_invalid_timestamp")

        latitude = self._finite_float(station.get("latitude"))
        longitude = self._finite_float(station.get("longitude"))
        if latitude is None or longitude is None:
            reasons.append("missing_coordinates")
        elif not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            reasons.append("invalid_coordinates")

        value = self._extract_metric_value(station, metric)
        if value is None:
            reasons.append("missing_or_invalid_metric")
        return reasons

    def _forecast_value(
        self,
        station_id: str,
        metric: str,
        forecast_hour: int,
    ) -> tuple[float, str, object | None]:
        history = self.station_service.get_forecast_history(station_id)
        valid_history = [item for item in history if self._history_point_is_usable(item, metric)]
        distinct_timestamps = {
            self._iso_or_none(item.get("measured_at") or item.get("timestamp"))
            for item in valid_history
        }
        distinct_timestamps.discard(None)
        if len(valid_history) < self.MIN_FORECAST_POINTS or len(distinct_timestamps) < self.MIN_FORECAST_POINTS:
            raise ServiceError(
                "insufficient_forecast_history",
                "At least three valid measurements with distinct timestamps are required",
                503,
                {"station_id": station_id, "history_points": len(valid_history)},
            )

        forecast = self.forecast_provider.forecast(
            station_id,
            valid_history,
            hours=forecast_hour,
            metric=metric,
        )
        horizons = forecast.get("horizons") or forecast.get("items") or []
        target = next(
            (
                item
                for item in horizons
                if item.get("hours_ahead", item.get("hour_offset")) == forecast_hour
            ),
            None,
        )
        if target is None:
            raise ServiceError(
                "spatial_forecast_unavailable",
                "The requested forecast horizon is unavailable",
                503,
                {"station_id": station_id, "forecast_hour": forecast_hour},
            )
        value = self._finite_float(target.get("predicted_value", target.get("value")))
        if value is None or not self._value_in_range(metric, value):
            raise ServiceError(
                "invalid_spatial_forecast",
                "Forecast value is missing or outside the accepted metric range",
                503,
                {"station_id": station_id, "metric": metric},
            )
        source = str(forecast.get("source") or forecast.get("model") or "")
        if not source:
            raise ServiceError(
                "invalid_spatial_forecast",
                "Forecast source is required",
                503,
                {"station_id": station_id},
            )
        forecast_at = self._aware_datetime(target.get("timestamp") or target.get("forecast_at"))
        if forecast_at is None:
            raise ServiceError(
                "invalid_spatial_forecast",
                "Forecast timestamp must be timezone-aware",
                503,
                {"station_id": station_id},
            )
        return value, source, forecast_at

    def _weather_context(self, forecast_hour: int) -> dict[str, Any]:
        try:
            weather = self.weather_provider.current_weather()
        except Exception as exc:
            raise ServiceError(
                "spatial_weather_unavailable",
                "Weather context is unavailable for wind-adjusted interpolation",
                503,
            ) from exc
        if weather.get("is_stale") is True:
            raise ServiceError(
                "spatial_weather_stale",
                "Stale weather context cannot drive the spatial model",
                503,
            )

        speed = self._finite_float(weather.get("wind_speed_ms", weather.get("wind_speed")))
        if speed is None or not 0 <= speed <= 60:
            raise ServiceError(
                "invalid_spatial_weather",
                "A valid wind speed is required for the spatial model",
                503,
            )
        direction = self._finite_float(
            weather.get("wind_direction_deg", weather.get("wind_direction"))
        )
        assumptions: list[str] = []
        if direction is None:
            direction = float(self.DEFAULT_WIND_DIRECTION_DEG)
            assumptions.append("wind_direction_uses_documented_simulator_assumption")
        if not 0 <= direction <= 360:
            raise ServiceError(
                "invalid_spatial_weather",
                "Wind direction must be between 0 and 360 degrees",
                503,
            )
        if forecast_hour > 0:
            assumptions.append("current_wind_held_constant_for_forecast_horizon")

        source = str(weather.get("source") or "")
        if not source:
            raise ServiceError(
                "invalid_spatial_weather",
                "Weather source is required for the spatial model",
                503,
            )
        observed_at = self._aware_datetime(weather.get("observed_at"))
        if observed_at is None:
            raise ServiceError(
                "invalid_spatial_weather",
                "Weather observed_at must be timezone-aware",
                503,
            )
        return {
            "wind_speed_ms": speed,
            "wind_direction_deg": int(round(direction)) % 360,
            "source": source,
            "observed_at": observed_at.astimezone(UTC).isoformat(),
            "is_fallback": bool(weather.get("is_fallback", False)),
            "is_stale": False,
            "assumptions": assumptions,
        }

    def _require_spatial_coverage(
        self,
        station_inputs: list[dict[str, Any]],
        excluded: dict[str, list[str]],
        metric: str,
        forecast_hour: int,
    ) -> None:
        unique_coordinates = {(item["lat"], item["lon"]) for item in station_inputs}
        if len(station_inputs) < self.MIN_STATIONS or len(unique_coordinates) < self.MIN_STATIONS:
            raise ServiceError(
                "insufficient_spatial_data",
                "At least three fresh stations with distinct coordinates are required",
                503,
                {
                    "metric": metric,
                    "forecast_hour": forecast_hour,
                    "stations_required": self.MIN_STATIONS,
                    "stations_usable": len(station_inputs),
                    "stations_excluded": sorted(excluded),
                    "exclusion_reasons": excluded,
                },
            )

    def _build_grid(
        self,
        station_inputs: list[dict[str, Any]],
        *,
        metric: str,
        wind_speed_ms: float,
        wind_direction_deg: int,
    ) -> list[dict[str, Any]]:
        latitude_step = (self.LAT_MAX - self.LAT_MIN) / (self.GRID_ROWS - 1)
        longitude_step = (self.LON_MAX - self.LON_MIN) / (self.GRID_COLS - 1)
        grid_points: list[dict[str, Any]] = []

        for row in range(self.GRID_ROWS):
            latitude = round(self.LAT_MIN + row * latitude_step, 5)
            for column in range(self.GRID_COLS):
                longitude = round(self.LON_MIN + column * longitude_step, 5)
                if not self._is_inside_boundary(latitude, longitude):
                    continue
                value = round(
                    self._interpolate_value_at(
                        latitude,
                        longitude,
                        station_inputs,
                        wind_speed_ms=wind_speed_ms,
                        wind_direction_deg=wind_direction_deg,
                    ),
                    1,
                )
                grid_points.append(
                    {
                        "lat": latitude,
                        "lon": longitude,
                        "value": value,
                        "intensity": self._compute_intensity(metric, value),
                        "level": self._compute_level(metric, value),
                    }
                )
        return grid_points

    @classmethod
    def _interpolate_value_at(
        cls,
        latitude: float,
        longitude: float,
        station_inputs: list[dict[str, Any]],
        *,
        wind_speed_ms: float,
        wind_direction_deg: int,
    ) -> float:
        wind_radians = math.radians(wind_direction_deg)
        wind_x = math.sin(wind_radians)
        wind_y = math.cos(wind_radians)
        weighted_sum = 0.0
        weight_sum = 0.0

        for station in station_inputs:
            latitude_distance = (latitude - station["lat"]) * 111.0
            longitude_distance = (longitude - station["lon"]) * 103.0
            distance = math.hypot(latitude_distance, longitude_distance)
            if distance <= cls.IDW_EPSILON_KM:
                return float(station["value"])

            direction_cosine = (
                longitude_distance / distance * wind_x
                + latitude_distance / distance * wind_y
            )
            effective_distance = cls._effective_distance(
                distance,
                direction_cosine=direction_cosine,
                wind_speed_ms=wind_speed_ms,
            )
            weight = 1.0 / ((effective_distance + cls.IDW_EPSILON_KM) ** cls.IDW_POWER)
            weight_sum += weight
            weighted_sum += weight * float(station["value"])

        if weight_sum <= 0:
            raise ServiceError(
                "spatial_interpolation_failed",
                "Spatial interpolation produced no usable weights",
                503,
            )
        return weighted_sum / weight_sum

    @staticmethod
    def _effective_distance(
        distance_km: float,
        *,
        direction_cosine: float,
        wind_speed_ms: float,
    ) -> float:
        wind_strength = min(0.6, max(0.0, wind_speed_ms) * 0.08)
        dispersion_factor = 1.0 - max(-1.0, min(1.0, direction_cosine)) * wind_strength
        return max(distance_km * max(0.2, dispersion_factor), 0.0001)

    @classmethod
    def _normalise_metric(cls, metric: str) -> str:
        normalised = cls.METRIC_ALIASES.get(metric.lower(), metric.lower())
        if normalised not in cls.METRIC_UNITS:
            raise ServiceError(
                "invalid_spatial_metric",
                "Unsupported spatial heatmap metric",
                422,
                {"metric": metric, "allowed": sorted(cls.METRIC_UNITS)},
            )
        return normalised

    @staticmethod
    def _validate_forecast_hour(forecast_hour: int) -> None:
        if isinstance(forecast_hour, bool) or not isinstance(forecast_hour, int):
            raise ServiceError(
                "invalid_spatial_forecast_hour",
                "forecast_hour must be an integer between 0 and 24",
                422,
            )
        if not 0 <= forecast_hour <= 24:
            raise ServiceError(
                "invalid_spatial_forecast_hour",
                "forecast_hour must be between 0 and 24",
                422,
                {"forecast_hour": forecast_hour},
            )

    @classmethod
    def _extract_metric_value(cls, station: dict[str, Any], metric: str) -> float | None:
        raw_value = station.get(metric)
        if metric == "aqi" and raw_value is None:
            pm25 = cls._finite_float(station.get("pm25"))
            raw_value = pm25_aqi(pm25) if pm25 is not None else None
        value = cls._finite_float(raw_value)
        if value is None or not cls._value_in_range(metric, value):
            return None
        return value

    @classmethod
    def _history_point_is_usable(cls, item: dict[str, Any], metric: str) -> bool:
        if item.get("quality_flag") not in {None, "valid"}:
            return False
        if not item.get("source"):
            return False
        timestamp = item.get("measured_at") or item.get("timestamp")
        if cls._aware_datetime(timestamp) is None:
            return False
        return cls._extract_metric_value(item, metric) is not None

    @classmethod
    def _value_in_range(cls, metric: str, value: float) -> bool:
        minimum, maximum = cls.METRIC_RANGES[metric]
        return minimum <= value <= maximum

    @staticmethod
    def _finite_float(value: object) -> float | None:
        if isinstance(value, bool):
            return None
        try:
            parsed = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return parsed if math.isfinite(parsed) else None

    @staticmethod
    def _aware_datetime(value: object) -> datetime | None:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        return parsed if parsed.tzinfo is not None else None

    @classmethod
    def _iso_or_none(cls, value: object) -> str | None:
        parsed = cls._aware_datetime(value)
        return parsed.astimezone(UTC).isoformat() if parsed else None

    @staticmethod
    def _compute_level(metric: str, value: float) -> str:
        if metric == "aqi":
            if value <= 50:
                return "good"
            if value <= 100:
                return "moderate"
            if value <= 150:
                return "unhealthy_sensitive"
            if value <= 200:
                return "unhealthy"
            if value <= 300:
                return "very_unhealthy"
            return "hazardous"
        if metric == "pm25":
            if value <= 12.0:
                return "good"
            if value <= 35.4:
                return "moderate"
            if value <= 55.4:
                return "unhealthy_sensitive"
            if value <= 150.4:
                return "unhealthy"
            return "very_unhealthy"
        if metric == "co2":
            if value <= 700:
                return "good"
            if value <= 1000:
                return "moderate"
            if value <= 1500:
                return "unhealthy_sensitive"
            return "unhealthy"
        if metric == "noise_db":
            if value <= 55:
                return "good"
            if value <= 70:
                return "moderate"
            return "unhealthy"
        if value <= 32:
            return "good"
        if value <= 36:
            return "moderate"
        return "unhealthy"

    @staticmethod
    def _compute_intensity(metric: str, value: float) -> float:
        if metric == "aqi":
            intensity = value / 250.0
        elif metric == "pm25":
            intensity = value / 120.0
        elif metric == "co2":
            intensity = (value - 400.0) / 1200.0
        elif metric == "noise_db":
            intensity = (value - 35.0) / 60.0
        else:
            intensity = (value - 22.0) / 20.0
        return round(min(1.0, max(0.0, intensity)), 3)
