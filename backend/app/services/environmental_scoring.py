from __future__ import annotations

import math
from typing import Any, Literal


class EnvironmentalScoringEngine:
    """
    Multi-Factor Environmental Suitability Scoring Engine.
    Computes weighted normalized scores [0..100] for candidate POIs and areas based on
    activity profile, environmental metrics, and user health sensitivity.
    """

    ACTIVITY_WEIGHTS = {
        "running": {"aqi": 0.40, "pm25": 0.25, "temperature": 0.15, "noise": 0.10, "distance": 0.10},
        "walking": {"aqi": 0.30, "pm25": 0.20, "temperature": 0.20, "noise": 0.15, "distance": 0.15},
        "children_play": {"aqi": 0.45, "pm25": 0.30, "temperature": 0.15, "noise": 0.10, "distance": 0.00},
        "elderly_stroll": {"aqi": 0.45, "pm25": 0.20, "temperature": 0.20, "noise": 0.10, "distance": 0.05},
        "dining_outdoor": {"aqi": 0.35, "pm25": 0.20, "temperature": 0.25, "noise": 0.20, "distance": 0.00},
        "general": {"aqi": 0.40, "pm25": 0.30, "temperature": 0.15, "noise": 0.15, "distance": 0.00},
    }

    @classmethod
    def score_candidate(
        cls,
        candidate: dict[str, Any],
        activity: str = "general",
        user_group: Literal["normal", "sensitive", "outdoor_sport"] = "normal",
        distance_m: float | None = None,
    ) -> dict[str, Any]:
        weights = cls.ACTIVITY_WEIGHTS.get(activity, cls.ACTIVITY_WEIGHTS["general"])

        aqi = float(candidate.get("aqi") or 50.0)
        pm25 = float(candidate.get("pm25") or 25.0)
        temp = float(candidate.get("temperature") or 28.0)
        noise = float(candidate.get("noise_db") or 55.0)

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
                raw_score *= 0.65  # Stronger penalty for sensitive groups
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

            # Bonus for dedicated pedestrian surface & zero vehicles
            bonus = 0.0
            if "Không có xe" in r.get("traffic_conflict", "") or "Phố đi bộ" in r.get("traffic_conflict", ""):
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
        Evaluates whether vigorous outdoor aerobic exercise is medically safe.
        Pivots to indoor alternatives if AQI/PM2.5 or temperature reaches hazardous thresholds.
        """
        aqi = float(metrics.get("aqi") or 50.0)
        pm25 = float(metrics.get("pm25") or 25.0)
        temp = float(metrics.get("temperature") or 28.0)

        # Thresholds: Sensitive groups have stricter cutoff
        aqi_limit = 100.0 if user_group == "sensitive" else 150.0
        pm25_limit = 50.0 if user_group == "sensitive" else 75.0

        if aqi > aqi_limit or pm25 > pm25_limit:
            return {
                "safe": False,
                "reason": "severe_air_pollution",
                "aqi": aqi,
                "pm25": pm25,
                "warning": (
                    f"Chỉ số AQI {int(aqi)} (PM2.5 {pm25} µg/m³) vượt ngưỡng an toàn cho vận động ngoài trời. "
                    "Khi chạy bộ hoặc tập cardio ngoài trời, lưu lượng thông khí phổi tăng gấp 5–10 lần, "
                    "khiến phế nang hấp thụ lượng lớn bụi mịn gây kích ứng phế quản."
                ),
            }

        if temp > 36.5:
            return {
                "safe": False,
                "reason": "extreme_heat",
                "temperature": temp,
                "warning": (
                    f"Nhiệt độ ngoài trời {temp}°C quá cao, có nguy cơ sốc nhiệt, mất nước nhanh và kiệt sức."
                ),
            }

        if temp < 10.0:
            return {
                "safe": False,
                "reason": "extreme_cold",
                "temperature": temp,
                "warning": f"Nhiệt độ ngoài trời {temp}°C rét đậm, hít thở không khí lạnh sâu có thể gây co thắt phế quản.",
            }

        return {"safe": True, "reason": "normal", "aqi": aqi, "pm25": pm25, "temperature": temp}


environmental_scoring = EnvironmentalScoringEngine()
