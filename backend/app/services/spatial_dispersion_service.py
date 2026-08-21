from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from .air_quality import pm25_aqi, aqi_category
from .station_service import StationService


class SpatialDispersionService:
    """
    Inverse Distance Weighting (IDW) interpolation engine with wind dispersion vector
    strictly clipped to the polygon boundary of Vinhomes Ocean Park 1.
    """

    # Exact Ocean Park 1 Boundary Polygon
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

    # Bounding Box Coordinates matching polygon
    LAT_MIN = 20.9840
    LAT_MAX = 21.0050
    LON_MIN = 105.9330
    LON_MAX = 105.9630

    # Grid Resolution
    GRID_ROWS = 36
    GRID_COLS = 36

    def __init__(self, station_service: StationService) -> None:
        self.station_service = station_service

    @classmethod
    def _is_inside_boundary(cls, lat: float, lon: float) -> bool:
        """Ray-casting algorithm to test if (lat, lon) is strictly within Ocean Park 1 boundary."""
        poly = cls.BOUNDARY_POLYGON
        n = len(poly)
        inside = False
        p1_lat, p1_lon = poly[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = poly[i % n]
            if min(p1_lat, p2_lat) < lat <= max(p1_lat, p2_lat):
                if lon <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        x_inters = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                    if p1_lon == p2_lon or lon <= x_inters:
                        inside = not inside
            p1_lat, p1_lon = p2_lat, p2_lon
        return inside

    def calculate_heatmap(
        self,
        metric: str = "aqi",
        forecast_hour: int = 0,
    ) -> dict[str, Any]:
        metric = metric.lower()
        if metric not in {"aqi", "pm25", "co2", "noise_db", "temperature"}:
            metric = "aqi"

        stations = self.station_service.list_stations()
        valid_stations = [s for s in stations if s.get("latitude") and s.get("longitude")]

        if not valid_stations:
            valid_stations = self.station_service._fallback_stations()

        # Simulated wind conditions
        wind_speed_ms = 3.2 + (forecast_hour * 0.4)
        wind_direction_deg = (135 + forecast_hour * 10) % 360
        wind_rad = math.radians(wind_direction_deg)
        wind_vec_x = math.sin(wind_rad)
        wind_vec_y = math.cos(wind_rad)

        station_data = []
        for s in valid_stations:
            val = self._extract_metric_value(s, metric)
            if forecast_hour > 0:
                drift_factor = 1.0 + (math.sin(forecast_hour * 0.8) * 0.15)
                val = round(val * drift_factor, 1)
            station_data.append({
                "lat": float(s["latitude"]),
                "lon": float(s["longitude"]),
                "val": float(val),
            })

        lat_step = (self.LAT_MAX - self.LAT_MIN) / (self.GRID_ROWS - 1)
        lon_step = (self.LON_MAX - self.LON_MIN) / (self.GRID_COLS - 1)

        grid_points: list[dict[str, Any]] = []

        power = 2.0
        epsilon = 0.0001

        for r in range(self.GRID_ROWS):
            curr_lat = round(self.LAT_MIN + r * lat_step, 5)
            for c in range(self.GRID_COLS):
                curr_lon = round(self.LON_MIN + c * lon_step, 5)

                # Strictly clip grid points to Ocean Park 1 boundary polygon
                if not self._is_inside_boundary(curr_lat, curr_lon):
                    continue

                sum_weights = 0.0
                sum_weighted_vals = 0.0

                for st in station_data:
                    d_lat = (curr_lat - st["lat"]) * 111.0
                    d_lon = (curr_lon - st["lon"]) * 103.0
                    dist = math.sqrt(d_lat * d_lat + d_lon * d_lon)

                    # Wind dispersion effect: adjust effective distance
                    if dist > 0.001 and wind_speed_ms > 0:
                        norm_dx = d_lon / dist
                        norm_dy = d_lat / dist
                        cos_theta = norm_dx * wind_vec_x + norm_dy * wind_vec_y
                        dispersion_factor = 1.0 - (cos_theta * min(0.6, wind_speed_ms * 0.08))
                        effective_dist = max(dist * max(0.2, dispersion_factor), epsilon)
                    else:
                        effective_dist = max(dist, epsilon)

                    w = 1.0 / (effective_dist ** power)
                    sum_weights += w
                    sum_weighted_vals += w * st["val"]

                interpolated_val = sum_weighted_vals / sum_weights if sum_weights > 0 else 0.0
                interpolated_val = round(interpolated_val, 1)

                level = self._compute_level(metric, interpolated_val)
                intensity = self._compute_intensity(metric, interpolated_val)

                grid_points.append({
                    "lat": curr_lat,
                    "lon": curr_lon,
                    "value": interpolated_val,
                    "intensity": intensity,
                    "level": level,
                })

        return {
            "metric": metric,
            "forecast_hour": forecast_hour,
            "source": "spatial_idw_dispersion_model",
            "model_version": "idw-dispersion-v1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wind_speed_ms": round(wind_speed_ms, 1),
            "wind_direction_deg": int(wind_direction_deg),
            "grid_points": grid_points,
            "disclaimer": "Mô hình nội suy trực quan hóa IDW kết hợp vector khí tượng mô phỏng trong ranh giới Vinhomes Ocean Park 1.",
        }

    @staticmethod
    def _extract_metric_value(station: dict[str, Any], metric: str) -> float:
        if metric == "aqi":
            if station.get("aqi") is not None:
                return float(station["aqi"])
            pm = station.get("pm25")
            return float(pm25_aqi(pm) or 50.0)
        elif metric == "pm25":
            return float(station.get("pm25") or 35.0)
        elif metric == "co2":
            return float(station.get("co2") or 600.0)
        elif metric == "noise_db":
            return float(station.get("noise_db") or 55.0)
        elif metric == "temperature":
            return float(station.get("temperature") or 30.5)
        return 50.0

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
        elif metric == "pm25":
            if value <= 12.0:
                return "good"
            if value <= 35.4:
                return "moderate"
            if value <= 55.4:
                return "unhealthy_sensitive"
            if value <= 150.4:
                return "unhealthy"
            return "very_unhealthy"
        elif metric == "co2":
            if value <= 700:
                return "good"
            if value <= 1000:
                return "moderate"
            if value <= 1500:
                return "unhealthy_sensitive"
            return "unhealthy"
        elif metric == "noise_db":
            if value <= 55:
                return "good"
            if value <= 70:
                return "moderate"
            return "unhealthy"
        elif metric == "temperature":
            if value <= 32:
                return "good"
            if value <= 36:
                return "moderate"
            return "unhealthy"
        return "moderate"

    @staticmethod
    def _compute_intensity(metric: str, value: float) -> float:
        if metric == "aqi":
            return round(min(1.0, max(0.0, value / 250.0)), 3)
        elif metric == "pm25":
            return round(min(1.0, max(0.0, value / 120.0)), 3)
        elif metric == "co2":
            return round(min(1.0, max(0.0, (value - 400.0) / 1200.0)), 3)
        elif metric == "noise_db":
            return round(min(1.0, max(0.0, (value - 35.0) / 60.0)), 3)
        elif metric == "temperature":
            return round(min(1.0, max(0.0, (value - 22.0) / 20.0)), 3)
        return 0.5
