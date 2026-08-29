from __future__ import annotations

import math
from typing import Any, Literal


class EnvironmentalScoringEngine:
    """
    Multi-Factor Environmental Suitability & Route Exposure Scoring Engine.
    Computes weighted normalized scores [0..100] and line-integral spatial exposure
    for candidate POIs, areas, and road network polylines based on activity profile,
    continuous IDW environmental fields, and user health sensitivity.
    """

    ACTIVITY_WEIGHTS = {
        "running": {"aqi": 0.40, "pm25": 0.25, "temperature": 0.15, "noise": 0.10, "distance": 0.10},
        "walking": {"aqi": 0.30, "pm25": 0.20, "temperature": 0.20, "noise": 0.15, "distance": 0.15},
        "children_play": {"aqi": 0.45, "pm25": 0.30, "temperature": 0.15, "noise": 0.10, "distance": 0.00},
        "elderly_stroll": {"aqi": 0.45, "pm25": 0.20, "temperature": 0.20, "noise": 0.10, "distance": 0.05},
        "dining_outdoor": {"aqi": 0.35, "pm25": 0.20, "temperature": 0.25, "noise": 0.20, "distance": 0.00},
        "general": {"aqi": 0.40, "pm25": 0.30, "temperature": 0.15, "noise": 0.15, "distance": 0.00},
    }

    # Canonical physical sensor positions from data/stations.json. A request
    # snapshot may override these coordinates, but POI proxy coordinates must
    # not be used to score a road segment.
    STATION_COORDINATES = {
        "S01": (21.0008, 105.9428),
        "S02": (20.9975, 105.9430),
        "S03": (20.9953, 105.9500),
        "S04": (20.9898, 105.9467),
        "S05": (20.9910, 105.9560),
    }

    @staticmethod
    def _required_metric(values: dict[str, Any], name: str) -> float:
        value = values.get(name)
        if isinstance(value, bool) or value is None:
            raise ValueError(f"grounded environmental metric is required: {name}")
        number = float(value)
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"grounded environmental metric is invalid: {name}")
        return number

    @classmethod
    def calculate_distance_m(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @classmethod
    def sample_polyline_points(
        cls,
        coords: list[list[float]],
        step_m: float = 35.0,
    ) -> list[tuple[float, float, float]]:
        """
        Samples equi-spaced points along polyline coordinates.
        Returns list of (lat, lng, segment_distance_m).
        """
        if not coords:
            return []
        if len(coords) == 1:
            return [(coords[0][0], coords[0][1], 0.0)]

        samples: list[tuple[float, float, float]] = []

        for i in range(len(coords) - 1):
            lat1, lon1 = coords[i][0], coords[i][1]
            lat2, lon2 = coords[i + 1][0], coords[i + 1][1]
            seg_dist = cls.calculate_distance_m(lat1, lon1, lat2, lon2)

            if seg_dist <= step_m or seg_dist < 1.0:
                samples.append((lat1, lon1, max(1.0, seg_dist)))
            else:
                num_steps = max(1, math.ceil(seg_dist / step_m))
                sub_dist = seg_dist / num_steps
                for s in range(num_steps):
                    frac = s / num_steps
                    s_lat = lat1 + (lat2 - lat1) * frac
                    s_lon = lon1 + (lon2 - lon1) * frac
                    samples.append((s_lat, s_lon, sub_dist))

        samples.append((coords[-1][0], coords[-1][1], 0.0))
        return samples

    @classmethod
    def interpolate_environment_at_coord(
        cls,
        lat: float,
        lon: float,
        station_data_map: dict[str, dict[str, Any]],
        wind_speed_ms: float = 3.0,
        wind_direction_deg: int = 135,
    ) -> dict[str, Any]:
        """Wind-adjusted IDW interpolation from request-scoped station facts."""
        wind_radians = math.radians(wind_direction_deg)
        wind_x = math.sin(wind_radians)
        wind_y = math.cos(wind_radians)
        wind_strength = min(0.6, max(0.0, wind_speed_ms) * 0.08)

        total_weight = 0.0
        weighted_metrics = {
            "pm25": 0.0,
            "aqi": 0.0,
            "co2": 0.0,
            "noise_db": 0.0,
            "temperature": 0.0,
        }

        source_weights: list[tuple[float, str]] = []
        for st_id, canonical_coords in cls.STATION_COORDINATES.items():
            st_data = station_data_map.get(st_id)
            if not st_data:
                continue
            required = ("pm25", "aqi", "co2", "noise_db", "temperature")
            if any(st_data.get(key) is None for key in required):
                continue
            # Coordinates are immutable station registry metadata, not an
            # environmental fallback. Environmental metrics remain mandatory.
            st_lat = float(st_data.get("latitude", canonical_coords[0]))
            st_lon = float(st_data.get("longitude", canonical_coords[1]))

            lat_dist_km = (lat - st_lat) * 111.0
            lon_dist_km = (lon - st_lon) * 103.0
            dist_km = math.hypot(lat_dist_km, lon_dist_km)

            if dist_km <= 0.0001:
                return {
                    "pm25": float(st_data["pm25"]),
                    "aqi": float(st_data["aqi"]),
                    "co2": float(st_data["co2"]),
                    "noise_db": float(st_data["noise_db"]),
                    "temperature": float(st_data["temperature"]),
                    "source_station_ids": [st_id],
                }

            direction_cosine = (lon_dist_km / dist_km * wind_x + lat_dist_km / dist_km * wind_y)
            dispersion_factor = 1.0 - max(-1.0, min(1.0, direction_cosine)) * wind_strength
            effective_dist_km = max(dist_km * max(0.2, dispersion_factor), 0.0001)

            w = 1.0 / (effective_dist_km ** 2.0)
            total_weight += w
            source_weights.append((w, st_id))

            weighted_metrics["pm25"] += w * float(st_data["pm25"])
            weighted_metrics["aqi"] += w * float(st_data["aqi"])
            weighted_metrics["co2"] += w * float(st_data["co2"])
            weighted_metrics["noise_db"] += w * float(st_data["noise_db"])
            weighted_metrics["temperature"] += w * float(st_data["temperature"])

        if total_weight <= 0:
            raise ValueError("route exposure requires at least one grounded station")

        result = {k: v / total_weight for k, v in weighted_metrics.items()}
        result["source_station_ids"] = [
            station_id for _, station_id in sorted(source_weights, reverse=True)[:3]
        ]
        return result

    @staticmethod
    def _segment_level(aqi: float, pm25: float) -> str:
        if aqi <= 50.0 and pm25 <= 25.0:
            return "good"
        if aqi <= 100.0 and pm25 <= 50.0:
            return "moderate"
        if aqi <= 150.0 and pm25 <= 75.0:
            return "unhealthy_sensitive"
        return "unhealthy"

    @classmethod
    def build_route_environment_segments(
        cls,
        route_coords: list[list[float]],
        station_data_map: dict[str, dict[str, Any]],
        wind_speed_ms: float = 3.0,
        wind_direction_deg: int = 135,
        step_m: float = 35.0,
    ) -> list[dict[str, Any]]:
        """Split a route into short drawable sections and score each midpoint."""
        if len(route_coords) < 2:
            return []

        timestamps = [
            str(item.get("timestamp"))
            for item in station_data_map.values()
            if item.get("timestamp")
        ]
        observed_at = max(timestamps) if timestamps else None
        segments: list[dict[str, Any]] = []

        for index in range(len(route_coords) - 1):
            start = route_coords[index]
            end = route_coords[index + 1]
            distance_m = cls.calculate_distance_m(start[0], start[1], end[0], end[1])
            divisions = max(1, math.ceil(distance_m / max(5.0, step_m)))

            for division in range(divisions):
                start_fraction = division / divisions
                end_fraction = (division + 1) / divisions
                sub_start = [
                    start[0] + (end[0] - start[0]) * start_fraction,
                    start[1] + (end[1] - start[1]) * start_fraction,
                ]
                sub_end = [
                    start[0] + (end[0] - start[0]) * end_fraction,
                    start[1] + (end[1] - start[1]) * end_fraction,
                ]
                midpoint = [
                    (sub_start[0] + sub_end[0]) / 2.0,
                    (sub_start[1] + sub_end[1]) / 2.0,
                ]
                environment = cls.interpolate_environment_at_coord(
                    lat=midpoint[0],
                    lon=midpoint[1],
                    station_data_map=station_data_map,
                    wind_speed_ms=wind_speed_ms,
                    wind_direction_deg=wind_direction_deg,
                )
                aqi = round(float(environment["aqi"]), 1)
                pm25 = round(float(environment["pm25"]), 1)
                segments.append(
                    {
                        "segment_index": len(segments),
                        "coordinates": [
                            [round(sub_start[0], 6), round(sub_start[1], 6)],
                            [round(sub_end[0], 6), round(sub_end[1], 6)],
                        ],
                        "distance_m": round(distance_m / divisions, 1),
                        "aqi": aqi,
                        "pm25": pm25,
                        "co2": round(float(environment["co2"]), 1),
                        "noise_db": round(float(environment["noise_db"]), 1),
                        "temperature": round(float(environment["temperature"]), 1),
                        "level": cls._segment_level(aqi, pm25),
                        "source": "spatial_idw_route_segment",
                        "source_station_ids": environment.get("source_station_ids", []),
                        "observed_at": observed_at,
                    }
                )
        return segments

    @classmethod
    def evaluate_route_spatial_exposure(
        cls,
        route_coords: list[list[float]],
        station_data_map: dict[str, dict[str, Any]],
        wind_speed_ms: float = 3.0,
        wind_direction_deg: int = 135,
        user_group: str = "normal",
        target_km: float | None = None,
        traffic_conflict: str = "",
        surface: str = "",
    ) -> dict[str, Any]:
        """
        Calculates exact line-integral environmental exposure along the entire route polyline.
        Computes Mean AQI/PM2.5, P90 percentiles, pollution hotspots, and composite suitability score.
        """
        segments = cls.build_route_environment_segments(
            route_coords=route_coords,
            station_data_map=station_data_map,
            wind_speed_ms=wind_speed_ms,
            wind_direction_deg=wind_direction_deg,
        )
        if not segments:
            return {
                "mean_aqi": 50.0,
                "mean_pm25": 25.0,
                "mean_temperature": 28.0,
                "mean_noise_db": 55.0,
                "mean_co2": 420.0,
                "p90_aqi": 50.0,
                "p90_pm25": 25.0,
                "hotspot_distance_m": 0.0,
                "hotspot_ratio": 0.0,
                "exposure_score": 75.0,
                "total_distance_m": 0.0,
                "environment_segments": [],
                "segment_count": 0,
            }

        total_dist_m = 0.0
        weighted_aqi = 0.0
        weighted_pm25 = 0.0
        weighted_temp = 0.0
        weighted_noise = 0.0
        weighted_co2 = 0.0

        all_aqis: list[float] = []
        all_pm25s: list[float] = []
        hotspot_dist_m = 0.0
        good_dist_m = 0.0
        moderate_dist_m = 0.0
        unhealthy_dist_m = 0.0

        for segment in segments:
            aqi_val = float(segment["aqi"])
            pm25_val = float(segment["pm25"])
            all_aqis.append(aqi_val)
            all_pm25s.append(pm25_val)

            effective_d = max(1.0, float(segment["distance_m"]))
            total_dist_m += effective_d
            weighted_aqi += aqi_val * effective_d
            weighted_pm25 += pm25_val * effective_d
            weighted_temp += float(segment["temperature"]) * effective_d
            weighted_noise += float(segment["noise_db"]) * effective_d
            weighted_co2 += float(segment["co2"]) * effective_d

            # Environmental zone classification (Good <= 50, Moderate 51..100, Unhealthy > 100)
            if aqi_val <= 50.0 and pm25_val <= 25.0:
                good_dist_m += effective_d
            elif aqi_val <= 100.0 and pm25_val <= 50.0:
                moderate_dist_m += effective_d
            else:
                unhealthy_dist_m += effective_d
                hotspot_dist_m += effective_d

        mean_aqi = round(weighted_aqi / total_dist_m, 1)
        mean_pm25 = round(weighted_pm25 / total_dist_m, 1)
        mean_temp = round(weighted_temp / total_dist_m, 1)
        mean_noise = round(weighted_noise / total_dist_m, 1)
        mean_co2 = round(weighted_co2 / total_dist_m, 1)

        # Percentiles & Extrema
        sorted_aqis = sorted(all_aqis)
        sorted_pm25s = sorted(all_pm25s)
        p90_idx = min(len(sorted_aqis) - 1, int(len(sorted_aqis) * 0.90))
        p90_aqi = round(sorted_aqis[p90_idx], 1)
        p90_pm25 = round(sorted_pm25s[p90_idx], 1)
        median_aqi = round(sorted_aqis[len(sorted_aqis) // 2], 1)
        max_aqi = round(sorted_aqis[-1], 1)
        max_pm25 = round(sorted_pm25s[-1], 1)

        hotspot_ratio = round(hotspot_dist_m / total_dist_m, 3)
        good_pct = int(round((good_dist_m / total_dist_m) * 100))
        moderate_pct = int(round((moderate_dist_m / total_dist_m) * 100))
        unhealthy_pct = max(0, 100 - good_pct - moderate_pct)

        # 1. Base Score calculation
        aqi_sub = max(0.0, min(100.0, 100.0 - (mean_aqi / 2.2)))
        pm25_sub = max(0.0, min(100.0, 100.0 - (mean_pm25 * 1.33)))
        temp_sub = max(0.0, min(100.0, 100.0 - abs(mean_temp - 25.0) * 5.0))
        noise_sub = max(0.0, min(100.0, 100.0 - max(0.0, mean_noise - 50.0) * 3.0))

        raw_score = (0.40 * aqi_sub) + (0.25 * pm25_sub) + (0.15 * temp_sub) + (0.10 * noise_sub) + 10.0

        # 2. Surface & Traffic Conflict Bonus
        bonus = 0.0
        if "cao su" in surface.lower() or "park_track" in surface.lower():
            bonus += 5.0  # Rubber running track shock absorption
        if "cấm" in traffic_conflict.lower() or "100%" in traffic_conflict.lower() or "zero" in traffic_conflict.lower():
            bonus += 4.0  # Zero traffic conflict

        # 3. Hotspot & Health Profile Penalties
        hotspot_penalty = (35.0 if user_group == "sensitive" else 18.0) * hotspot_ratio

        if user_group == "sensitive":
            if mean_aqi > 100.0 or mean_pm25 > 35.0:
                raw_score *= 0.65
            elif mean_aqi > 50.0:
                raw_score *= 0.85

        # 4. Detour & Excessive Distance Penalties
        actual_km = total_dist_m / 1000.0
        detour_penalty = 0.0
        if target_km and target_km > 0.5:
            delta_km = abs(actual_km - target_km)
            detour_penalty = min(50.0, delta_km * 22.0)
        else:
            # Default sensible jogging distance is ~3.5 km; heavily penalize marathon-length detours (> 5.5km)
            if actual_km > 5.0:
                excess_km = actual_km - 5.0
                detour_penalty = min(60.0, excess_km * 20.0)
            elif actual_km < 1.5:
                detour_penalty = min(25.0, (1.5 - actual_km) * 15.0)

        final_score = round(max(0.0, min(100.0, raw_score + bonus - hotspot_penalty - detour_penalty)), 1)

        if final_score >= 75.0:
            tier = "recommended"
        elif final_score >= 55.0:
            tier = "alternative"
        elif final_score >= 35.0:
            tier = "caution"
        else:
            tier = "avoid"

        return {
            "mean_aqi": mean_aqi,
            "median_aqi": median_aqi,
            "max_aqi": max_aqi,
            "max_pm25": max_pm25,
            "mean_pm25": mean_pm25,
            "mean_temperature": mean_temp,
            "mean_noise_db": mean_noise,
            "mean_co2": mean_co2,
            "p90_aqi": p90_aqi,
            "p90_pm25": p90_pm25,
            "distance_above_threshold_m": round(hotspot_dist_m),
            "hotspot_distance_m": round(hotspot_dist_m),
            "hotspot_ratio": hotspot_ratio,
            "exposure_score": final_score,
            "tier": tier,
            "total_distance_m": round(total_dist_m),
            "actual_distance_km": round(actual_km, 1),
            "environment_distribution": {
                "good_percent": good_pct,
                "moderate_percent": moderate_pct,
                "unhealthy_percent": unhealthy_pct,
                "good_distance_m": round(good_dist_m),
                "moderate_distance_m": round(moderate_dist_m),
                "unhealthy_distance_m": round(unhealthy_dist_m),
            },
            "environment_segments": segments,
            "segment_count": len(segments),
            "breakdown": {
                "aqi_sub": round(aqi_sub, 1),
                "pm25_sub": round(pm25_sub, 1),
                "temp_sub": round(temp_sub, 1),
                "noise_sub": round(noise_sub, 1),
                "bonus": bonus,
                "hotspot_penalty": round(hotspot_penalty, 1),
                "detour_penalty": round(detour_penalty, 1),
            },
        }

    @classmethod
    def rank_route_candidates(
        cls,
        candidates: list[dict[str, Any]],
        station_data_map: dict[str, dict[str, Any]],
        wind_speed_ms: float = 3.0,
        wind_direction_deg: int = 135,
        user_group: str = "normal",
        target_km: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Ranks candidate routes objectively using line-integral spatial exposure.
        Computes comparative reduction percentage vs baseline route.
        """
        evaluated: list[dict[str, Any]] = []

        for cand in candidates:
            coords = cand.get("coordinates", [])
            if not isinstance(coords, list) or len(coords) < 2:
                continue
            exposure = cls.evaluate_route_spatial_exposure(
                route_coords=coords,
                station_data_map=station_data_map,
                wind_speed_ms=wind_speed_ms,
                wind_direction_deg=wind_direction_deg,
                user_group=user_group,
                target_km=target_km or cand.get("target_requested_km"),
                traffic_conflict=cand.get("traffic_conflict", ""),
                surface=cand.get("surface", ""),
            )

            # Route total pollution exposure metric = mean_pm25 * distance_km
            total_pm25_exposure = round(exposure["mean_pm25"] * exposure["actual_distance_km"], 1)

            final_dist_km = (
                round(cand["target_requested_km"], 1)
                if cand.get("distance_constraint_satisfied") and cand.get("target_requested_km")
                else exposure["actual_distance_km"]
            )

            access_dist_m = float(cand.get("access_distance_m", 0.0))
            access_penalty = 0.0
            if access_dist_m > 1000.0:
                access_penalty = min(35.0, (access_dist_m - 1000.0) * 0.025)
            adjusted_score = round(max(0.0, exposure["exposure_score"] - access_penalty), 1)

            cand_updated = {
                **cand,
                "score": adjusted_score,
                "tier": exposure["tier"],
                "aqi": exposure["mean_aqi"],
                "mean_aqi": exposure["mean_aqi"],
                "median_aqi": exposure.get("median_aqi", exposure["mean_aqi"]),
                "max_aqi": exposure.get("max_aqi", exposure["p90_aqi"]),
                "pm25": exposure["mean_pm25"],
                "mean_pm25": exposure["mean_pm25"],
                "temperature": exposure["mean_temperature"],
                "noise_db": exposure["mean_noise_db"],
                "co2": exposure["mean_co2"],
                "p90_aqi": exposure["p90_aqi"],
                "p90_pm25": exposure["p90_pm25"],
                "distance_above_threshold_m": exposure.get("distance_above_threshold_m", exposure["hotspot_distance_m"]),
                "hotspot_distance_m": exposure["hotspot_distance_m"],
                "hotspot_ratio": exposure["hotspot_ratio"],
                "distance_km": final_dist_km,
                "distance_m": exposure["total_distance_m"],
                "total_pm25_exposure": total_pm25_exposure,
                "environment_distribution": exposure["environment_distribution"],
                "environment_segments": exposure["environment_segments"],
                "segment_count": exposure["segment_count"],
                "timestamp": (
                    exposure["environment_segments"][0].get("observed_at")
                    if exposure["environment_segments"]
                    else None
                ),
                "exposure_breakdown": {
                    **exposure["breakdown"],
                    "access_penalty": round(access_penalty, 1),
                },
            }
            evaluated.append(cand_updated)

        # Sort descending by score
        evaluated.sort(key=lambda x: x["score"], reverse=True)

        if not evaluated:
            return []

        # Calculate comparative reduction vs the least clean / baseline route
        baseline = evaluated[-1]
        baseline_pm25 = max(1.0, float(baseline["pm25"]))

        for idx, item in enumerate(evaluated):
            item["rank"] = idx + 1
            cand_pm25 = float(item["pm25"])
            reduction_pct = round(max(0.0, (baseline_pm25 - cand_pm25) / baseline_pm25) * 100.0, 1)
            item["exposure_reduction_pct"] = reduction_pct

        return evaluated

    @classmethod
    def score_candidate(
        cls,
        candidate: dict[str, Any],
        activity: str = "general",
        user_group: Literal["normal", "sensitive", "outdoor_sport"] = "normal",
        distance_m: float | None = None,
    ) -> dict[str, Any]:
        weights = cls.ACTIVITY_WEIGHTS.get(activity, cls.ACTIVITY_WEIGHTS["general"])

        aqi = cls._required_metric(candidate, "aqi")
        pm25 = cls._required_metric(candidate, "pm25")
        temp = cls._required_metric(candidate, "temperature")
        noise = cls._required_metric(candidate, "noise_db")

        # 1. Sub-score: AQI (100 = 0 AQI, 0 = 250+ AQI)
        aqi_sub = max(0.0, min(100.0, 100.0 - (aqi / 2.2)))

        # 2. Sub-score: PM2.5 (100 = 0 ug/m3, 0 = 75+ ug/m3)
        pm25_sub = max(0.0, min(100.0, 100.0 - (pm25 * 1.33)))

        # 3. Sub-score: Temperature (Ideal 22-28C)
        if 22.0 <= temp <= 28.0:
            temp_sub = 100.0
        elif temp > 28.0:
            temp_sub = max(0.0, 100.0 - (temp - 28.0) * 8.0)
        else:
            temp_sub = max(0.0, 100.0 - (22.0 - temp) * 6.0)

        # 4. Sub-score: Noise (Ideal < 55dB, poor > 80dB)
        noise_sub = max(0.0, min(100.0, 100.0 - max(0.0, noise - 50.0) * 3.0))

        # 5. Sub-score: Distance
        if distance_m is not None:
            dist_sub = max(0.0, min(100.0, 100.0 - (distance_m / 40.0)))
        else:
            dist_sub = 80.0

        # Raw weighted score
        raw_score = (
            weights["aqi"] * aqi_sub
            + weights["pm25"] * pm25_sub
            + weights["temperature"] * temp_sub
            + weights["noise"] * noise_sub
            + weights["distance"] * dist_sub
        )

        # Health Profile Sensitivity Adjustments
        if user_group == "sensitive":
            if aqi > 100.0 or pm25 > 35.0:
                raw_score *= 0.65
            elif aqi > 50.0:
                raw_score *= 0.85

        final_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Determine suitability tier
        if final_score >= 75.0:
            tier = "recommended"
        elif final_score >= 55.0:
            tier = "alternative"
        elif final_score >= 35.0:
            tier = "caution"
        else:
            tier = "avoid"

        return {
            "score": final_score,
            "tier": tier,
            "breakdown": {
                "aqi_score": round(aqi_sub, 1),
                "pm25_score": round(pm25_sub, 1),
                "temperature_score": round(temp_sub, 1),
                "noise_score": round(noise_sub, 1),
                "distance_score": round(dist_sub, 1),
            },
        }

    @classmethod
    def rank_candidates(
        cls,
        candidates: list[dict[str, Any]],
        activity: str = "general",
        user_group: str = "normal",
        user_location: tuple[float, float] | None = None,
    ) -> list[dict[str, Any]]:
        scored = []
        for c in candidates:
            dist_m = None
            if user_location and c.get("latitude") and c.get("longitude"):
                from .spatial_registry import spatial_registry
                dist_m = spatial_registry.calculate_distance_m(
                    user_location[0], user_location[1], c["latitude"], c["longitude"]
                )

            res = cls.score_candidate(c, activity=activity, user_group=user_group, distance_m=dist_m)
            scored.append({**c, **res, "distance_m": round(dist_m) if dist_m else None})

        scored.sort(key=lambda x: x["score"], reverse=True)
        for idx, item in enumerate(scored):
            item["rank"] = idx + 1
        return scored

    @classmethod
    def rank_routes(
        cls,
        routes: list[dict[str, Any]],
        user_group: str = "normal",
        user_location: tuple[float, float] | None = None,
    ) -> list[dict[str, Any]]:
        scored = []
        for r in routes:
            dist_m = None
            if user_location and r.get("start_point"):
                from .spatial_registry import spatial_registry
                dist_m = spatial_registry.calculate_distance_m(
                    user_location[0], user_location[1], r["start_point"]["lat"], r["start_point"]["lng"]
                )

            res = cls.score_candidate(r, activity="running", user_group=user_group, distance_m=dist_m)

            bonus = 0.0
            if "Không có xe" in r.get("traffic_conflict", "") or "Phố đi bộ" in r.get("traffic_conflict", "") or "Cấm xe" in r.get("traffic_conflict", ""):
                bonus += 4.0
            if "cao su" in r.get("surface", "").lower():
                bonus += 3.0

            final_route_score = round(min(100.0, res["score"] + bonus), 1)

            if final_route_score >= 75.0:
                tier = "recommended"
            elif final_route_score >= 55.0:
                tier = "alternative"
            elif final_route_score >= 35.0:
                tier = "caution"
            else:
                tier = "avoid"

            scored.append(
                {
                    **r,
                    "score": final_route_score,
                    "tier": tier,
                    "breakdown": res["breakdown"],
                    "distance_to_start_m": round(dist_m) if dist_m else None,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        for idx, item in enumerate(scored):
            item["rank"] = idx + 1
        return scored

    @classmethod
    def check_outdoor_exercise_safety(
        cls,
        metrics: dict[str, Any],
        user_group: str = "normal",
    ) -> dict[str, Any]:
        """
        Applies versioned demo-policy gates for outdoor activity wording.

        This is not a medical safety assessment. Missing environmental facts fail
        closed instead of being replaced by demo defaults.
        """
        aqi = cls._required_metric(metrics, "aqi")
        pm25 = cls._required_metric(metrics, "pm25")
        temp = cls._required_metric(metrics, "temperature")

        # Thresholds: Sensitive groups have stricter cutoff
        aqi_limit = 100.0 if user_group == "sensitive" else 150.0
        pm25_limit = 50.0 if user_group == "sensitive" else 75.0

        if aqi > aqi_limit or pm25 > pm25_limit:
            reason = "unhealthy_for_sensitive_groups" if user_group == "sensitive" and aqi <= 150 else "severe_air_pollution"
            return {
                "safe": False,
                "reason": reason,
                "user_group": user_group,
                "aqi": aqi,
                "pm25": pm25,
                "warning": (
                    f"AQI {int(aqi)} và PM2.5 {pm25} µg/m³ vượt ngưỡng policy demo cho hoạt động ngoài trời. "
                    "Cân nhắc giảm hoạt động ngoài trời; đây không phải tư vấn y tế."
                ),
            }

        if temp > 36.5:
            return {
                "safe": False,
                "reason": "extreme_heat",
                "temperature": temp,
                "warning": f"Nhiệt độ ngoài trời {temp}°C vượt ngưỡng policy demo; cân nhắc hoạt động trong nhà.",
            }

        if temp < 10.0:
            return {
                "safe": False,
                "reason": "extreme_cold",
                "temperature": temp,
                "warning": f"Nhiệt độ ngoài trời {temp}°C dưới ngưỡng policy demo; cân nhắc hoạt động trong nhà.",
            }

        return {"safe": True, "reason": "normal", "aqi": aqi, "pm25": pm25, "temperature": temp}


environmental_scoring = EnvironmentalScoringEngine()
