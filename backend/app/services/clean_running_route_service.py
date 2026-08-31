from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .database import ServiceError
from .forecast_service import InsufficientForecastHistory, trend_forecast
from .inhaled_dose_service import VENTILATION_RATE_M3_MIN
from .road_graph_router import road_graph_router

ROUTE_POLICY_VERSION = "route-policy-v1"
ROUTE_DISCLAIMER = (
    "Tuyến demo dựa trên graph đóng gói và dữ liệu simulator; "
    "cần tự kiểm tra điều kiện đường thực tế."
)
DEFAULT_PACE_MIN_KM = Decimal("6.5")
DEFAULT_PACE_MIN_KM_BY_ACTIVITY = {
    "walking": Decimal("12.0"),
    "running": DEFAULT_PACE_MIN_KM,
    "cycling": Decimal("4.0"),
}


def _finite(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("finite number required") from exc
    if not math.isfinite(number):
        raise ValueError("finite number required")
    return number


def _timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return value.astimezone(UTC)


class CleanRunningRouteService:
    def __init__(
        self,
        station_service: Any,
        *,
        observation_max_age_seconds: int = 300,
        min_forecast_confidence: float = 0.60,
        forecast_max_age_seconds: int = 900,
        clock: Any | None = None,
    ) -> None:
        self.station_service = station_service
        self.observation_max_age_seconds = int(observation_max_age_seconds)
        self.min_forecast_confidence = float(min_forecast_confidence)
        self.forecast_max_age_seconds = int(forecast_max_age_seconds)
        self._clock = clock or (lambda: datetime.now(UTC))

    def recommend(
        self,
        *,
        origin: dict[str, Any],
        target_distance_km: float,
        pace_minutes_per_km: float | None = None,
        data_mode: str = "current",
        forecast_hour: int | None = None,
        activity: str = "running",
    ) -> dict[str, Any]:
        lat, lon, origin_source = self._validate_request(
            origin,
            target_distance_km,
            pace_minutes_per_km,
            data_mode,
            forecast_hour,
            activity,
        )
        metadata = dict(getattr(road_graph_router, "GRAPH_METADATA", {}) or {})
        if not metadata or metadata.get("source") not in {"curated_demo_graph", "openstreetmap_snapshot"}:
            raise ServiceError("road_graph_unavailable", "Packaged road graph is unavailable", 503)
        if not self._inside_boundary(lat, lon, metadata.get("boundary") or []):
            raise ServiceError("route_origin_out_of_bounds", "Route origin is outside the demo area", 422)

        snap = road_graph_router.snap_origin_to_network(lat, lon, activity=activity)
        max_snap_distance_m = 400 if activity == "cycling" else 250
        if not snap.get("is_valid") or float(snap.get("snap_distance_m", math.inf)) > max_snap_distance_m:
            raise ServiceError(
                "route_origin_snap_failed",
                f"Route origin could not be snapped within {max_snap_distance_m} m",
                422,
                {"max_snap_distance_m": max_snap_distance_m},
            )

        station_inputs, forecast_target = self._station_inputs(data_mode, forecast_hour)
        station_pm25 = {station_id: item["pm25"] for station_id, item in station_inputs.items()}
        raw_candidates = road_graph_router.generate_candidate_routes_from_origin(
            origin_lat=lat,
            origin_lng=lon,
            target_km=target_distance_km,
            station_pm25_map=station_pm25,
            origin_source=origin_source,
            activity=activity,
        )
        candidates: list[dict[str, Any]] = []
        seen_edge_paths: set[tuple[str, ...]] = set()
        for raw in raw_candidates:
            raw_edge_ids = tuple(str(value) for value in (raw.get("edge_ids") or []) if value)
            if not raw_edge_ids or raw_edge_ids in seen_edge_paths:
                continue
            seen_edge_paths.add(raw_edge_ids)
            try:
                if raw.get("base_circuit_id") == "route_target_tailored":
                    edge_chunks, coordinates = self._validated_partial_edge_chunks(
                        raw.get("coordinates") or [],
                        raw_edge_ids,
                    )
                    edge_ids = tuple(edge_id for edge_id, _coords in edge_chunks)
                else:
                    edge_ids = raw_edge_ids
                    edge_chunks, coordinates = self._edge_chunks(snap["node_id"], edge_ids)
            except ValueError:
                continue
            distance_m = sum(road_graph_router.calculate_polyline_distance_m(chunk[1]) for chunk in edge_chunks)
            distance_km = distance_m / 1000
            if abs(distance_km - target_distance_km) / target_distance_km > 0.20:
                continue
            candidates.append(
                self._evaluate_candidate(
                    snapped_node=str(snap["node_id"]),
                    edge_ids=edge_ids,
                    edge_chunks=edge_chunks,
                    coordinates=coordinates,
                    distance_m=distance_m,
                    target_distance_km=target_distance_km,
                    pace_minutes_per_km=Decimal(
                        str(pace_minutes_per_km) if pace_minutes_per_km is not None else str(DEFAULT_PACE_MIN_KM_BY_ACTIVITY[activity])
                    ),
                    station_inputs=station_inputs,
                    data_mode=data_mode,
                    forecast_target=forecast_target,
                    graph_id=str(metadata["graph_id"]),
                    graph_version=str(metadata["graph_version"]),
                    activity=activity,
                )
            )
            if len(candidates) == 3:
                break
        if not candidates:
            raise ServiceError("route_not_found", "No graph route satisfies the requested distance", 503)

        max_mass = max(item["_mass_raw"] for item in candidates)
        for item in candidates:
            exposure_cost = item["_mass_raw"] / max_mass if max_mass > 0 else Decimal("0")
            distance_cost = min(
                Decimal("1"),
                abs(item["_distance_raw_km"] - Decimal(str(target_distance_km))) / Decimal(str(target_distance_km)),
            )
            item["_distance_deviation"] = distance_cost
            item["total_cost"] = float(Decimal("0.70") * exposure_cost + Decimal("0.30") * distance_cost)
        candidates.sort(
            key=lambda item: (
                item["total_cost"],
                item["_mass_raw"],
                item["_distance_deviation"],
                item["route_id"],
            )
        )
        selected = candidates[0]
        comparable = [
            item
            for item in candidates[1:]
            if abs(item["_distance_raw_km"] - selected["_distance_raw_km"]) / selected["_distance_raw_km"]
            <= Decimal("0.10")
        ]
        baseline = min(comparable, key=lambda item: (item["_distance_raw_km"], item["route_id"])) if comparable else None
        selected["baseline"] = None
        selected["exposure_reduction_pct"] = None
        if baseline is not None and baseline["_mass_raw"] > 0 and baseline["route_id"] != selected["route_id"]:
            selected["baseline"] = {
                "route_id": baseline["route_id"],
                "distance_km": baseline["distance_km"],
                "estimated_inhaled_mass_ug": baseline["estimated_inhaled_mass_ug"],
            }
            reduction = (baseline["_mass_raw"] - selected["_mass_raw"]) / baseline["_mass_raw"] * Decimal("100")
            selected["exposure_reduction_pct"] = float(
                reduction.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )

        for private_key in [key for key in selected if key.startswith("_")]:
            selected.pop(private_key, None)
        selected.pop("total_cost", None)
        selected.update(
            {
                "activity": activity,
                "target_distance_km": target_distance_km,
                "target_requested_km": target_distance_km,
                "distance_constraint_satisfied": True,
                "planning_method": "grounded_packaged_graph_candidate_ranking",
                "data_mode": data_mode,
                "graph": {
                    "graph_id": metadata["graph_id"],
                    "graph_version": metadata["graph_version"],
                    "graph_source": metadata["source"],
                    "snapshot_at": metadata.get("snapshot_at"),
                    "checksum_sha256": metadata["checksum_sha256"],
                    "license": metadata["license"],
                    "attribution": metadata["attribution"],
                    "node_count": metadata.get("node_count"),
                    "edge_count": metadata.get("edge_count"),
                    "poi_count": metadata.get("poi_count"),
                },
                "policy_version": ROUTE_POLICY_VERSION,
                "assumptions": [f"pace_minutes_per_km={DEFAULT_PACE_MIN_KM_BY_ACTIVITY[activity]}"] if pace_minutes_per_km is None else [],
                "disclaimer": ROUTE_DISCLAIMER,
                "origin": {
                    "source": origin_source,
                    "snapped_node_id": snap["node_id"],
                    "snap_distance_m": snap["snap_distance_m"],
                    "road_snap_coordinate": snap["road_snap_coordinate"],
                    "access_coordinates": snap["access_coordinates"],
                },
            }
        )
        return selected

    @staticmethod
    def _validate_request(
        origin: dict[str, Any],
        target_distance_km: float,
        pace_minutes_per_km: float | None,
        data_mode: str,
        forecast_hour: int | None,
        activity: str,
    ) -> tuple[float, float, str]:
        try:
            lat = _finite(origin.get("lat"))
            lon = _finite(origin.get("lon"))
            distance = _finite(target_distance_km)
        except (AttributeError, ValueError) as exc:
            raise ServiceError("route_target_out_of_range", "Route request is invalid", 422) from exc
        origin_source = str(origin.get("source") or "")
        if origin_source not in {"map_selection", "gps", "named_poi", "demo_default"}:
            raise ServiceError("route_origin_out_of_bounds", "origin.source is unsupported", 422)
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ServiceError("route_origin_out_of_bounds", "Route origin is invalid", 422)
        if not 1 <= distance <= 10:
            raise ServiceError("route_target_out_of_range", "target_distance_km must be between 1 and 10", 422)
        if activity not in DEFAULT_PACE_MIN_KM_BY_ACTIVITY:
            raise ServiceError("invalid_activity", "activity must be walking, running, or cycling", 422)
        if pace_minutes_per_km is not None:
            try:
                pace = _finite(pace_minutes_per_km)
            except ValueError as exc:
                raise ServiceError("route_target_out_of_range", "pace_minutes_per_km is invalid", 422) from exc
            if not 3 <= pace <= 20:
                raise ServiceError("route_target_out_of_range", "pace_minutes_per_km must be between 3 and 20", 422)
        if data_mode == "current" and forecast_hour is not None:
            raise ServiceError("invalid_forecast_hour", "forecast_hour must be null for current mode", 422)
        if data_mode == "forecast" and (
            isinstance(forecast_hour, bool) or not isinstance(forecast_hour, int) or not 1 <= forecast_hour <= 3
        ):
            raise ServiceError("invalid_forecast_hour", "forecast_hour must be between 1 and 3", 422)
        if data_mode not in {"current", "forecast"}:
            raise ServiceError("invalid_forecast_hour", "data_mode must be current or forecast", 422)
        return lat, lon, origin_source

    @staticmethod
    def _inside_boundary(lat: float, lon: float, boundary: list[list[float]]) -> bool:
        if len(boundary) < 4:
            return False
        inside = False
        j = len(boundary) - 1
        for i, point in enumerate(boundary):
            yi, xi = point
            yj, xj = boundary[j]
            if ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
            ):
                inside = not inside
            j = i
        return inside

    def _station_inputs(self, data_mode: str, forecast_hour: int | None) -> tuple[dict[str, dict[str, Any]], str | None]:
        now = self._clock().astimezone(UTC)
        inputs: dict[str, dict[str, Any]] = {}
        forecast_target: str | None = None
        for station in self.station_service.list_stations():
            station_id = str(station.get("station_id") or "")
            try:
                pm25 = _finite(station.get("pm25"))
                observed_at = _timestamp(station.get("updated_at"))
                latitude = _finite(station.get("latitude"))
                longitude = _finite(station.get("longitude"))
            except (ValueError, TypeError):
                continue
            if (
                not station_id
                or station.get("status") != "online"
                or station.get("freshness") != "fresh"
                or station.get("is_stale") is True
                or station.get("source") != "simulator"
                or pm25 < 0
                or not -1 <= (now - observed_at).total_seconds() <= self.observation_max_age_seconds
            ):
                continue
            item = {
                "pm25": pm25,
                "latitude": latitude,
                "longitude": longitude,
                "observed_at": observed_at.isoformat(),
                "source": "simulator",
            }
            if data_mode == "forecast":
                try:
                    forecast = trend_forecast(
                        self.station_service.get_forecast_history(station_id),
                        int(forecast_hour or 0),
                        metric="pm25",
                        generated_at=now,
                    )
                    generated_at = _timestamp(forecast.get("generated_at"))
                    confidence = _finite(forecast.get("confidence"))
                    point = next(
                        value
                        for value in forecast.get("items") or []
                        if value.get("hour_offset") == forecast_hour
                    )
                    point_value = _finite(point.get("value"))
                    target_at = _timestamp(point.get("forecast_at"))
                    source = str(point.get("source") or forecast.get("source") or "")
                    model_version = str(forecast.get("model_version") or "")
                except (InsufficientForecastHistory, StopIteration, TypeError, ValueError, ServiceError):
                    continue
                age_seconds = (now - generated_at).total_seconds()
                if (
                    forecast.get("freshness") != "fresh"
                    or not 0 <= age_seconds <= self.forecast_max_age_seconds
                    or confidence < self.min_forecast_confidence
                    or not source
                    or not model_version
                ):
                    continue
                item.update(
                    {
                        "pm25": point_value,
                        "observed_at": target_at.isoformat(),
                        "source": source,
                        "model_version": model_version,
                        "confidence": confidence,
                    }
                )
                forecast_target = target_at.isoformat()
            inputs[station_id] = item
        if len(inputs) < 3:
            code = "insufficient_forecast_quality" if data_mode == "forecast" else "insufficient_route_coverage"
            raise ServiceError(code, "At least three quality-gated stations are required", 503, {"available": len(inputs)})
        return inputs, forecast_target

    @staticmethod
    def _edge_chunks(start_node: str, edge_ids: tuple[str, ...]) -> tuple[list[tuple[str, list[list[float]]]], list[list[float]]]:
        edge_map = {str(edge["id"]): edge for edge in road_graph_router.EDGES}
        current = start_node
        chunks: list[tuple[str, list[list[float]]]] = []
        coordinates: list[list[float]] = []
        for edge_id in edge_ids:
            edge = edge_map.get(edge_id)
            if edge is None:
                raise ValueError("unknown edge")
            if edge["from"] == current:
                chunk = [list(value) for value in edge["coords"]]
                current = edge["to"]
            elif edge["to"] == current:
                chunk = [list(value) for value in reversed(edge["coords"])]
                current = edge["from"]
            else:
                raise ValueError("disconnected edge path")
            chunks.append((edge_id, chunk))
            coordinates.extend(chunk if not coordinates else chunk[1:])
        if len(coordinates) < 2:
            raise ValueError("empty path")
        return chunks, coordinates

    @staticmethod
    def _validated_partial_edge_chunks(
        raw_coordinates: list[list[float]],
        candidate_edge_ids: tuple[str, ...],
    ) -> tuple[list[tuple[str, list[list[float]]]], list[list[float]]]:
        """Validate a tailored mid-edge turn-around without inventing geometry."""
        coordinates = [[_finite(point[0]), _finite(point[1])] for point in raw_coordinates]
        if len(coordinates) < 2:
            raise ValueError("empty tailored path")
        edge_map = {str(edge["id"]): edge for edge in road_graph_router.EDGES}
        candidates = [edge_map[edge_id] for edge_id in dict.fromkeys(candidate_edge_ids) if edge_id in edge_map]
        exact_segments: dict[tuple[tuple[float, float], tuple[float, float]], str] = {}
        for edge in candidates:
            for first, second in zip(edge["coords"], edge["coords"][1:]):
                forward = ((float(first[0]), float(first[1])), (float(second[0]), float(second[1])))
                exact_segments[forward] = str(edge["id"])
                exact_segments[(forward[1], forward[0])] = str(edge["id"])
        chunks: list[tuple[str, list[list[float]]]] = []
        for start, end in zip(coordinates, coordinates[1:]):
            segment_key = ((start[0], start[1]), (end[0], end[1]))
            matched_edge_id = exact_segments.get(segment_key)
            if matched_edge_id is None:
                for edge in candidates:
                    for first, second in zip(edge["coords"], edge["coords"][1:]):
                        if CleanRunningRouteService._point_on_line(
                            start, first, second
                        ) and CleanRunningRouteService._point_on_line(end, first, second):
                            matched_edge_id = str(edge["id"])
                            break
                    if matched_edge_id:
                        break
            if matched_edge_id is None:
                raise ValueError("tailored coordinate is not on a packaged graph edge")
            chunks.append((matched_edge_id, [start, end]))
        return chunks, coordinates

    @staticmethod
    def _point_on_line(point: list[float], start: list[float], end: list[float]) -> bool:
        dy = end[0] - start[0]
        dx = end[1] - start[1]
        length_squared = dy * dy + dx * dx
        if length_squared == 0:
            return math.hypot(point[0] - start[0], point[1] - start[1]) <= 2e-6
        projection = ((point[0] - start[0]) * dy + (point[1] - start[1]) * dx) / length_squared
        if projection < -1e-6 or projection > 1 + 1e-6:
            return False
        projected = [start[0] + projection * dy, start[1] + projection * dx]
        return math.hypot(point[0] - projected[0], point[1] - projected[1]) <= 2e-6

    def _evaluate_candidate(
        self,
        *,
        snapped_node: str,
        edge_ids: tuple[str, ...],
        edge_chunks: list[tuple[str, list[list[float]]]],
        coordinates: list[list[float]],
        distance_m: float,
        target_distance_km: float,
        pace_minutes_per_km: Decimal,
        station_inputs: dict[str, dict[str, Any]],
        data_mode: str,
        forecast_target: str | None,
        graph_id: str,
        graph_version: str,
        activity: str,
    ) -> dict[str, Any]:
        distance_km_raw = Decimal(str(distance_m)) / Decimal("1000")
        duration_raw = distance_km_raw * pace_minutes_per_km
        raw_segments: list[dict[str, Any]] = []
        for edge_id, coords in edge_chunks:
            for index in range(len(coords) - 1):
                start, end = coords[index], coords[index + 1]
                line_distance = road_graph_router.calculate_distance_m(start[0], start[1], end[0], end[1])
                divisions = max(1, math.ceil(line_distance / 35.0))
                for division in range(divisions):
                    a = division / divisions
                    b = (division + 1) / divisions
                    sub_start = [start[0] + (end[0] - start[0]) * a, start[1] + (end[1] - start[1]) * a]
                    sub_end = [start[0] + (end[0] - start[0]) * b, start[1] + (end[1] - start[1]) * b]
                    midpoint = [(sub_start[0] + sub_end[0]) / 2, (sub_start[1] + sub_end[1]) / 2]
                    pm25, sources = self._idw_pm25(midpoint[0], midpoint[1], station_inputs)
                    segment_distance = Decimal(str(line_distance / divisions))
                    segment_duration = segment_distance / Decimal(str(distance_m)) * duration_raw
                    segment_mass = Decimal(str(pm25)) * VENTILATION_RATE_M3_MIN[activity] * segment_duration
                    raw_segments.append(
                        {
                            "edge_id": edge_id,
                            "coordinates": [
                                [round(sub_start[0], 6), round(sub_start[1], 6)],
                                [round(sub_end[0], 6), round(sub_end[1], 6)],
                            ],
                            "_distance": segment_distance,
                            "_duration": segment_duration,
                            "_mass": segment_mass,
                            "pm25": round(pm25, 2),
                            "source_station_ids": sources,
                        }
                    )
        if not raw_segments:
            raise ServiceError("route_not_found", "Route has no graph segments", 503)
        total_mass = sum((item["_mass"] for item in raw_segments), Decimal("0"))
        rounded_total_mass = total_mass.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        rounded_duration = duration_raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        segment_mass_sum = Decimal("0")
        segment_duration_sum = Decimal("0")
        observed_at = max(item["observed_at"] for item in station_inputs.values())
        segments = []
        for index, item in enumerate(raw_segments):
            is_last = index == len(raw_segments) - 1
            mass = (
                rounded_total_mass - segment_mass_sum
                if is_last
                else item["_mass"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            )
            duration = (
                rounded_duration - segment_duration_sum
                if is_last
                else item["_duration"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            )
            segment_mass_sum += mass
            segment_duration_sum += duration
            segments.append(
                {
                    "edge_id": item["edge_id"],
                    "coordinates": item["coordinates"],
                    "distance_m": float(item["_distance"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                    "duration_minutes": float(duration),
                    "pm25": item["pm25"],
                    "level": (
                        "critical"
                        if item["pm25"] >= 100
                        else "warning"
                        if item["pm25"] >= 50
                        else "moderate"
                        if item["pm25"] >= 25
                        else "good"
                    ),
                    "estimated_inhaled_mass_ug": float(mass),
                    "source_station_ids": item["source_station_ids"],
                    "observed_at": observed_at,
                    "source": "forecast_spatial_idw_route_segment" if data_mode == "forecast" else "spatial_idw_route_segment",
                }
            )
        route_hash_input = ":".join(
            [graph_id, graph_version, snapped_node, activity, *edge_ids, data_mode, forecast_target or "current"]
        )
        route_hash = hashlib.sha256(route_hash_input.encode("utf-8")).hexdigest()[:16]
        return {
            "route_id": f"{ROUTE_POLICY_VERSION}:{graph_id}:{route_hash}",
            "distance_km": float(distance_km_raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "duration_minutes": float(rounded_duration),
            "pace_minutes_per_km": float(pace_minutes_per_km),
            "coordinates": [[round(point[0], 6), round(point[1], 6)] for point in coordinates],
            "segments": segments,
            "estimated_inhaled_mass_ug": float(rounded_total_mass),
            "_mass_raw": total_mass,
            "_distance_raw_km": distance_km_raw,
            "_target": Decimal(str(target_distance_km)),
        }

    @staticmethod
    def _idw_pm25(lat: float, lon: float, station_inputs: dict[str, dict[str, Any]]) -> tuple[float, list[str]]:
        weights: list[tuple[float, str, float]] = []
        for station_id, item in station_inputs.items():
            distance = road_graph_router.calculate_distance_m(lat, lon, item["latitude"], item["longitude"])
            if distance <= 1:
                return float(item["pm25"]), [station_id]
            weight = 1 / ((distance / 1000) ** 2)
            weights.append((weight, station_id, float(item["pm25"])))
        if len(weights) < 3:
            raise ServiceError("insufficient_route_coverage", "At least three stations are required", 503)
        total_weight = sum(value[0] for value in weights)
        pm25 = sum(weight * value for weight, _, value in weights) / total_weight
        sources = [station_id for _, station_id, _ in sorted(weights, reverse=True)[:3]]
        return pm25, sources
