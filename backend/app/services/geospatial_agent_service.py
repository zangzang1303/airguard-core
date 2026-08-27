import json
import logging
import re
from typing import Any

from .conversational_agent_service import conversational_agent
from .database import ServiceError
from .environmental_scoring import environmental_scoring
from .prophet_forecast_service import prophet_service
from .response_composer import ResponseComposer, ResponseValidator, aqi_category_vi
from .spatial_registry import spatial_registry
from .temporal_resolver import temporal_resolver

logger = logging.getLogger(__name__)


def _aqi_category_vi(aqi: int | float | None) -> str:
    return aqi_category_vi(aqi)


class GeospatialAgentService:
    """
    End-to-End Geospatial Interactive AI Agent Engine.
    Processes user questions with spatial map context, evaluates live & forecast
    environmental metrics without hardcoding, and synthesizes natural-language answers
    with declarative Leaflet map actions.
    """

    def __init__(self, telemetry_engine: Any | None = None) -> None:
        self.telemetry_engine = telemetry_engine

    def process_query(
        self,
        message: str,
        user_id: str = "demo-user",
        station_id: str | None = None,
        map_context: dict[str, Any] | None = None,
        request_id: str = "geo-req-001",
        user_role: str = "resident",
        user_group: str = "normal",
        station_snapshots: dict[str, dict[str, Any]] | None = None,
        station_histories: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        map_context = map_context or {}
        q = message.lower().strip()

        conversation = conversational_agent.classify(
            message,
            station_id=station_id,
            map_context=map_context,
        )
        if conversation.intent != "domain":
            return conversational_agent.deterministic_response(conversation, request_id=request_id)

        # 1. Resolve Time Context (Live vs Forecast)
        time_ctx = temporal_resolver.resolve(q)
        is_forecast = time_ctx["is_forecast"]
        forecast_hour = time_ctx["forecast_hour"]

        # 2. Deterministic Origin & Coordinate Resolution with Precedence
        origin_lat = None
        origin_lng = None
        origin_source = "default_location"
        origin_label = "Trung tâm Vinhomes Ocean Park 1"

        # Priority 1: Explicit selected origin / clicked point on map
        if map_context.get("selected_origin"):
            so = map_context["selected_origin"]
            if isinstance(so, dict) and "lat" in so and "lng" in so:
                origin_lat = float(so["lat"])
                origin_lng = float(so["lng"])
                origin_source = so.get("source") or "map_selection"
                origin_label = so.get("name") or "Điểm đã chọn trên bản đồ"
        elif map_context.get("clicked_origin"):
            co = map_context["clicked_origin"]
            if isinstance(co, dict) and "lat" in co and "lng" in co:
                origin_lat = float(co["lat"])
                origin_lng = float(co["lng"])
                origin_source = "map_selection"
                origin_label = "Điểm đã chọn trên bản đồ"
        elif map_context.get("selected_point"):
            sp = map_context["selected_point"]
            if isinstance(sp, (list, tuple)) and len(sp) >= 2:
                origin_lat = float(sp[0])
                origin_lng = float(sp[1])
                origin_source = "map_selection"
                origin_label = "Điểm đã chọn trên bản đồ"
        elif "user_location" in map_context and map_context["user_location"]:
            uloc = map_context["user_location"]
            if isinstance(uloc, dict) and uloc.get("source") == "manual_click" and "lat" in uloc and "lng" in uloc:
                origin_lat = float(uloc["lat"])
                origin_lng = float(uloc["lng"])
                origin_source = "map_selection"
                origin_label = uloc.get("name") or "Điểm đã chọn trên bản đồ"

        # Priority 2: Explicit POI or coordinate mentioned in query string
        if origin_lat is None:
            explicit_poi, _ = spatial_registry.extract_location_in_query(q)
            if explicit_poi:
                origin_lat = float(explicit_poi["latitude"])
                origin_lng = float(explicit_poi["longitude"])
                origin_source = "query_poi"
                origin_label = explicit_poi["name"]

        # Priority 3: Current map selection (selected_location / selected_sensor)
        if origin_lat is None and map_context.get("selected_location"):
            sel_loc_name = str(map_context["selected_location"])
            poi_match = spatial_registry.find_poi_by_name(sel_loc_name)
            if poi_match:
                origin_lat = float(poi_match["latitude"])
                origin_lng = float(poi_match["longitude"])
                origin_source = "map_poi_selection"
                origin_label = poi_match["name"]

        # Priority 4: User location / GPS
        if origin_lat is None and "user_location" in map_context and map_context["user_location"]:
            uloc = map_context["user_location"]
            if isinstance(uloc, dict) and "lat" in uloc and "lng" in uloc:
                origin_lat = float(uloc["lat"])
                origin_lng = float(uloc["lng"])
                origin_source = "user_gps"
                origin_label = uloc.get("name") or "Vị trí GPS của bạn"
            elif isinstance(uloc, (list, tuple)) and len(uloc) >= 2:
                origin_lat = float(uloc[0])
                origin_lng = float(uloc[1])
                origin_source = "user_gps"
                origin_label = "Vị trí GPS của bạn"

        # Priority 5: Fallback default
        if origin_lat is None or origin_lng is None:
            origin_lat = 20.9938
            origin_lng = 105.9485
            origin_source = "default_location"
            origin_label = "Trung tâm Vinhomes Ocean Park 1"

        user_loc = (origin_lat, origin_lng)

        # 3. Detect Activity
        activity = "general"
        if any(w in q for w in ["chạy", "chạy bộ", "run", "running", "jogging", "jog"]):
            activity = "running"
        elif any(w in q for w in ["đi dạo", "tản bộ", "đi bộ", "walk", "walking"]):
            activity = "walking"
        elif any(w in q for w in ["trẻ em", "vui chơi", "sân chơi", "chơi", "bé", "con"]):
            activity = "children_play"
        elif any(w in q for w in ["người già", "người cao tuổi", "ông bà", "dưỡng sinh"]):
            activity = "elderly_stroll"
        elif any(w in q for w in ["ăn uống", "cafe", "cà phê", "ngoài trời", "ngồi"]):
            activity = "dining_outdoor"

        # 4. Use only request-scoped, system-of-record station inputs. The
        # in-memory engine is available solely through explicit test/demo injection.
        if station_snapshots is None:
            if self.telemetry_engine is None:
                raise ServiceError(
                    "geospatial_station_data_unavailable",
                    "Grounded station snapshots are required for geospatial analysis",
                    503,
                )
            if hasattr(self.telemetry_engine, "get_latest"):
                station_snapshots = {
                    station_id: self.telemetry_engine.get_latest(station_id)
                    for station_id in ["S01", "S02", "S03", "S04", "S05"]
                }
            else:
                station_snapshots = {
                    station["station_id"]: station
                    for station in self.telemetry_engine.get_current_stations()
                }
        if station_histories is None:
            station_histories = (
                self.telemetry_engine.get_all_histories(hours=48)
                if self.telemetry_engine is not None
                else {}
            )

        station_data_map = {}
        for s_id in ["S01", "S02", "S03", "S04", "S05"]:
            current_st = station_snapshots.get(s_id)
            if not self._usable_station_snapshot(current_st):
                continue
            if not is_forecast:
                station_data_map[s_id] = {
                    "station_id": s_id,
                    "latitude": current_st["latitude"],
                    "longitude": current_st["longitude"],
                    "pm25": current_st["pm25"],
                    "aqi": current_st["aqi"],
                    "co2": current_st["co2"],
                    "noise_db": current_st["noise_db"],
                    "temperature": current_st["temperature"],
                    "timestamp": current_st.get("measured_at") or current_st["updated_at"],
                    "source": current_st["source"],
                }
            else:
                history = station_histories.get(s_id, [])
                if len(history) < 3:
                    continue
                try:
                    metric_points = {
                        metric: self._forecast_point(s_id, history, forecast_hour, metric)
                        for metric in ("pm25", "co2", "noise_db", "temperature")
                    }
                except (KeyError, TypeError, ValueError, ServiceError):
                    continue

                from .air_quality import pm25_aqi

                pm25_point = metric_points["pm25"]
                predicted_pm25 = pm25_point["predicted_value"]
                station_data_map[s_id] = {
                    "station_id": s_id,
                    "latitude": current_st["latitude"],
                    "longitude": current_st["longitude"],
                    "pm25": predicted_pm25,
                    "aqi": pm25_aqi(predicted_pm25),
                    "co2": metric_points["co2"]["predicted_value"],
                    "noise_db": metric_points["noise_db"]["predicted_value"],
                    "temperature": metric_points["temperature"]["predicted_value"],
                    "timestamp": pm25_point["timestamp"],
                    "source": pm25_point["source"],
                    "lower_bound": pm25_point["lower_bound"],
                    "upper_bound": pm25_point["upper_bound"],
                }

        if len(station_data_map) < 3:
            raise ServiceError(
                "insufficient_geospatial_station_data",
                "At least three fresh grounded stations are required for geospatial analysis",
                503,
                {"available_station_ids": sorted(station_data_map)},
            )

        # 5. Populate All Candidate POIs with associated Station data or IDW interpolation
        candidate_pois = []
        for p in spatial_registry.list_pois():
            if p.get("is_interpolated"):
                interp_env = spatial_registry.interpolate_environment_at_point(
                    lat=p["latitude"],
                    lon=p["longitude"],
                    station_data_map=station_data_map,
                )
                cand = {**p, **interp_env}
            else:
                associated_st_id = p["sensor_id"]
                env = station_data_map.get(associated_st_id)
                if env is None:
                    continue
                cand = {
                    **p,
                    "pm25": env["pm25"],
                    "aqi": env["aqi"],
                    "co2": env["co2"],
                    "noise_db": env["noise_db"],
                    "temperature": env["temperature"],
                    "timestamp": env["timestamp"],
                    "is_interpolated": False,
                    "method": "direct_sensor_measurement",
                    "source_sensors": [associated_st_id],
                }
            candidate_pois.append(cand)

        # Rank all POIs dynamically
        ranked_pois = environmental_scoring.rank_candidates(
            candidate_pois, activity=activity, user_group=user_group, user_location=user_loc
        )

        # 5. Extract Custom Target Distance & Origin from User Query
        target_distance_km: float | None = None
        dist_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|cây|kilo|kilomet)", q)
        if dist_match:
            try:
                target_distance_km = float(dist_match.group(1))
            except ValueError:
                target_distance_km = None

        # Check if user mentioned starting place in query
        if not user_loc:
            if "sapphire" in q:
                user_loc = (20.9975, 105.9430)
            elif "san hô" in q or "san ho" in q:
                user_loc = (20.9935, 105.9405)
            elif "an đào" in q or "an dao" in q:
                user_loc = (20.9995, 105.9415)
            elif "vinuni" in q:
                user_loc = (20.9898, 105.9467)
            elif "hải âu" in q or "hai au" in q or "ocean" in q:
                user_loc = (20.9945, 105.9585)
            elif "sao biển" in q or "sao bien" in q:
                user_loc = (20.9985, 105.9525)

        # 6. Intent Determination & Dispatching

        # Intent: Out-of-Scope Domains (Medical, Real estate, Dining, Traffic)
        is_medical = any(w in q for w in ["uống thuốc", "thuốc gì", "bệnh gì", "bác sĩ", "chữa bệnh", "khám bệnh", "đau đầu", "sốt"])
        is_real_estate = any(w in q for w in ["giá nhà", "giá căn hộ", "mua chung cư", "thuê nhà", "giá bán", "bất động sản", "mặt bằng"])
        is_dining = any(w in q for w in ["quán ăn", "ăn gì ngon", "quán phở", "quán nhậu", "nhà hàng ngon", "quán cafe đẹp", "món ngon"])
        is_traffic = any(w in q for w in ["tắc đường", "kẹt xe", "ùn tắc giao thông", "xe buýt số"])
        if is_medical or is_real_estate or is_dining or is_traffic:
            return self._handle_general_out_of_scope_intent(q, request_id)

        # Intent: Weather / Rain / Precipitation (Out of measurement scope with microclimate fallback)
        is_rain_inquiry = any(
            w in q
            for w in [
                "mưa", "có mưa", "mưa không", "mưa rào", "lượng mưa", "mưa to", "mưa nhỏ",
                "mưa hay không", "bão", "sấm sét", "ngập lụt", "dông", "tuyết", "mưa bão"
            ]
        )
        if is_rain_inquiry:
            explicit_poi, _ = spatial_registry.extract_location_in_query(q)
            target_poi = None
            if explicit_poi:
                target_poi = next((p for p in ranked_pois if p["id"] == explicit_poi["id"]), explicit_poi)
            elif map_context.get("selected_location") or map_context.get("selected_sensor") or station_id:
                s_target = map_context.get("selected_sensor") or station_id
                target_poi = next(
                    (p for p in ranked_pois if p["id"] == map_context.get("selected_location") or p.get("sensor_id") == s_target),
                    ranked_pois[0],
                )
            return self._handle_rain_or_precipitation_intent(q, target_poi, time_ctx, request_id)

        # Intent: Unknown / Unrecognized Location Check
        explicit_poi, unrecognized_loc = spatial_registry.extract_location_in_query(q)
        if unrecognized_loc and not explicit_poi:
            return self._handle_unknown_location_intent(unrecognized_loc, request_id)

        # Intent A: Compare Locations (e.g. "so sánh sapphire và hồ ngọc trai", "an đào và sao biển")
        mentioned_pois = spatial_registry.find_all_pois_in_query(q)
        is_comparison = (
            len(mentioned_pois) >= 2
            or any(w in q for w in ["so sánh", "so voi", "so với", "hơn không", "tốt hơn", "khác nhau"])
            or (" và " in q and any(w in q for w in ["chỗ nào", "đâu", "khu nào", "tốt hơn", "sạch hơn", "ô nhiễm hơn"]))
        )
        if is_comparison and (len(mentioned_pois) >= 2 or len(ranked_pois) >= 2):
            return self._handle_comparison_intent(q, ranked_pois, time_ctx, request_id, candidates=mentioned_pois)

        # Intent B: Worst Location / Most Polluted Area
        is_worst_inquiry = (
            any(w in q for w in ["ô nhiễm nhất", "kém nhất", "xấu nhất", "nguy hiểm nhất", "tệ nhất"])
            and not any(w in q for w in ["ít ô nhiễm", "sạch nhất", "tốt nhất", "chạy", "tuyến", "đường", "cung đường", "lộ trình"])
            and target_distance_km is None
        )
        if is_worst_inquiry:
            return self._handle_worst_location_intent(ranked_pois, time_ctx, request_id)

        # Intent C: Indoor Activity Inquiry / Negation Pivot ("ngoài chạy bộ...", "trong nhà", "ở nhà", "indoor")
        is_indoor_inquiry = (
            any(w in q for w in ["trong nhà", "ở trong nhà", "indoor", "ở nhà", "phòng gym", "gym", "yoga", "bể bơi bốn mùa", "trong phòng"])
            or (
                any(w in q for w in ["thay vì", "khác", "không muốn", "đừng", "hạn chế"])
                and any(w in q for w in ["chạy", "chạy bộ", "ra ngoài"])
            )
            or (
                "ngoài " in q
                and not any(w in q for w in ["ngoài trời", "ngoài hồ", "ngoài công viên", "ngoài sân", "ra ngoài"])
                and any(w in q for w in ["chạy", "chạy bộ", "tập thể dục", "thể thao", "hoạt động"])
            )
        )
        if is_indoor_inquiry:
            return self._handle_explicit_indoor_intent(q, ranked_pois, time_ctx, request_id, user_loc=user_loc)

        # Intent 0: Running Route Recommendation (Personalized or General)
        is_route_query = (
            any(w in q for w in ["đoạn đường", "cung đường", "tuyến đường", "lộ trình", "đường chạy", "chạy bộ ở đâu", "tuyến chạy", "chạy ở đâu", "tuyến nào", "đường nào", "chạy bộ"])
            or target_distance_km is not None
            or (activity == "running" and any(w in q for w in ["đường", "tuyến", "đoạn", "ở đâu", "lộ trình", "nơi nào", "chỗ nào"]))
        )
        if is_route_query:
            from .road_graph_router import road_graph_router

            start_node, snap_dist_m = road_graph_router.find_nearest_node(origin_lat, origin_lng)
            max_origin_snap_distance = 250.0  # meters

            # Structured Debug Logging for Routing Origin Trace
            logger.info(
                "Running route origin trace: "
                + json.dumps(
                    {
                        "query": message,
                        "origin_source": origin_source,
                        "origin_label": origin_label,
                        "clicked_origin": {"lat": origin_lat, "lng": origin_lng},
                        "agent_origin": {"lat": origin_lat, "lng": origin_lng},
                        "routing_origin": {"lat": origin_lat, "lng": origin_lng},
                        "snapped_origin": {
                            "lat": road_graph_router.NODES[start_node]["lat"],
                            "lng": road_graph_router.NODES[start_node]["lng"],
                            "node": start_node,
                            "name": road_graph_router.NODES[start_node]["name"],
                        },
                        "snap_distance_m": round(snap_dist_m, 1),
                    },
                    ensure_ascii=False,
                )
            )

            # Max Snap Distance check (Section 8)
            if snap_dist_m > max_origin_snap_distance:
                headline = f"📍 **Mình chưa tìm thấy lối chạy bộ phù hợp đủ gần điểm bạn chọn (cách trục đường gần nhất khoảng {int(snap_dist_m)} m).**"
                advice = "Bạn có thể chọn một điểm gần các trục đường nội khu, công viên hoặc dải ven hồ trong khu đô thị Vinhomes Ocean Park 1 để mình vẽ lộ trình chính xác hơn."
                summary = f"{headline}\n\n{advice}"
                return {
                    "answer": {
                        "headline": headline,
                        "summary": summary,
                        "details": advice,
                        "highlights": [],
                        "recommendation": advice,
                        "map_feedback": "",
                        "data_note": "",
                    },
                    "response": summary,
                    "intent": "recommend_running_route",
                    "time_context": time_ctx,
                    "data_mode": time_ctx["type"],
                    "origin": {"source": origin_source, "lat": origin_lat, "lng": origin_lng, "label": origin_label},
                    "evidence": [],
                    "map_actions": [],
                    "request_id": request_id,
                }

            station_pm25_map = {
                station: float(values.get("pm25", 25.0))
                for station, values in station_data_map.items()
            }

            # 1. Generate real road-network candidate routes with Local-First strategy
            candidates = road_graph_router.generate_candidate_routes_from_origin(
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                target_km=target_distance_km,
                station_pm25_map=station_pm25_map,
                origin_source=origin_source,
                origin_label=origin_label,
            )

            # 2. Continuous Line-Integral Spatial Environmental Scoring along polyline coordinates
            ranked_routes = environmental_scoring.rank_route_candidates(
                candidates=candidates,
                station_data_map=station_data_map,
                user_group=user_group,
                target_km=target_distance_km,
            )

            if not ranked_routes:
                raise ServiceError(
                    "running_route_unavailable",
                    "No grounded road-network candidate is available from the selected origin",
                    503,
                    {"origin_source": origin_source},
                )

            best_route = ranked_routes[0]

            # 3. Medical Safety Gate for Aerobic Exercise
            safety_eval = environmental_scoring.check_outdoor_exercise_safety(
                {
                    "aqi": best_route.get("aqi", 50.0),
                    "pm25": best_route.get("pm25", 25.0),
                    "temperature": best_route.get("temperature", 28.0),
                },
                user_group=user_group,
            )
            if not safety_eval["safe"]:
                return self._handle_indoor_pivot_intent(
                    safety_eval=safety_eval,
                    user_location=(origin_lat, origin_lng),
                    time_ctx=time_ctx,
                    request_id=request_id,
                )

            return self._handle_running_route_intent(
                ranked_routes=ranked_routes,
                time_ctx=time_ctx,
                request_id=request_id,
                target_distance_km=target_distance_km,
                is_personalized=bool(origin_source != "default_location" or target_distance_km),
                origin_info={"source": origin_source, "lat": origin_lat, "lng": origin_lng, "label": origin_label},
            )

        # Intent C: Specific Metric Focus (Noise, Temp, PM2.5/CO2) or Single Location / Follow-up Inquiry
        is_noise_inquiry = any(w in q for w in ["độ ồn", "tiếng ồn", "ồn không", "yên tĩnh", "ồn ào", "ồn thế nào"])
        is_temp_inquiry = any(w in q for w in ["nhiệt độ", "nóng không", "mát không", "nhiệt độ bao nhiêu", "bao nhiêu độ"])

        target_poi = None
        explicit_station_id = self._extract_explicit_station_id(q)
        if explicit_station_id:
            station_poi = next(
                (
                    poi for poi in ranked_pois
                    if poi.get("sensor_id") == explicit_station_id and not poi.get("is_interpolated")
                ),
                None,
            )
            # A station ID is an explicit telemetry request, not a request for
            # whichever named POI happens to share that sensor or is selected
            # on the map. Keep the POI coordinates for map focus, but present
            # the answer and annotations as the requested station.
            if station_poi:
                target_poi = {
                    **station_poi,
                    "short_name": f"Trạm {explicit_station_id}",
                    "name": f"Trạm quan trắc {explicit_station_id}",
                }
        elif explicit_poi:
            target_poi = next((p for p in ranked_pois if p["id"] == explicit_poi["id"]), explicit_poi)
        elif map_context.get("selected_location"):
            sel_id = map_context["selected_location"]
            target_poi = next(
                (p for p in ranked_pois if p["id"] == sel_id or p["short_name"].lower() in str(sel_id).lower()),
                None,
            )
            if not target_poi:
                poi_from_sel = spatial_registry.find_poi_by_name(str(sel_id))
                if poi_from_sel:
                    target_poi = next((p for p in ranked_pois if p["id"] == poi_from_sel["id"]), None)
            if not target_poi:
                target_poi = ranked_pois[0]
        elif map_context.get("selected_sensor") or station_id:
            s_target = map_context.get("selected_sensor") or station_id
            target_poi = next((p for p in ranked_pois if p.get("sensor_id") == s_target and not p.get("is_interpolated")), ranked_pois[0])

        if target_poi is not None:
            if is_noise_inquiry:
                return self._handle_specific_noise_intent(target_poi, time_ctx, request_id)
            if is_temp_inquiry:
                return self._handle_specific_temp_intent(target_poi, time_ctx, request_id)

            # If user asks a specific question about a location or follow-up
            is_single_loc_query = (
                explicit_station_id is not None
                or explicit_poi is not None
                or is_forecast
                or map_context.get("selected_location")
                or map_context.get("selected_sensor")
                or station_id
                or any(w in q for w in [
                    "thế nào", "sao", "chất lượng", "bao nhiêu", "có tốt",
                    "chỗ này", "ở đây", "khu này", "nơi này", "vị trí này",
                    "thì sao", "như nào", "aqi", "pm25", "pm2.5", "không khí"
                ])
            )
            if is_single_loc_query:
                return self._handle_single_location_intent(target_poi, time_ctx, request_id)

        if is_noise_inquiry:
            return self._handle_specific_noise_intent(ranked_pois[0], time_ctx, request_id)
        if is_temp_inquiry:
            return self._handle_specific_temp_intent(ranked_pois[0], time_ctx, request_id)

        # Intent D: Best Location / Outdoor Activity Recommendation (Default rich flow)
        return self._handle_recommendation_intent(
            ranked_pois, activity, time_ctx, request_id, user_group, user_loc=user_loc
        )

    # -------------------------------------------------------------
    # INTENT HANDLER: Weather / Rain / Precipitation (Out of Scope with Microclimate Context)
    # -------------------------------------------------------------
    # INTENT HANDLER: Weather / Rain / Precipitation (Out of Scope with Microclimate Context)
    # -------------------------------------------------------------
    def _handle_rain_or_precipitation_intent(
        self,
        q: str,
        poi: dict[str, Any] | None,
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        composed = ResponseComposer.compose_precipitation_unsupported(
            poi=poi,
            time_ctx=time_ctx,
            request_id=request_id,
        )

        if poi:
            map_actions = [
                {"type": "clear_ai_layer"},
                {
                    "type": "highlight_point",
                    "target_id": poi["id"],
                    "lat": poi["latitude"],
                    "lng": poi["longitude"],
                    "name": poi["short_name"],
                    "style": "info",
                },
                {
                    "type": "add_annotation",
                    "target_id": poi["id"],
                    "lat": poi["latitude"],
                    "lng": poi["longitude"],
                    "title": f"Thông tin tại {poi['short_name']}",
                    "subtitle": f"{poi['temperature']}°C • AQI {poi['aqi']} (Không đo lượng mưa)",
                    "badge": "Ngoài phạm vi đo mưa",
                    "style": "info",
                },
                {
                    "type": "fly_to",
                    "lat": poi["latitude"],
                    "lng": poi["longitude"],
                    "zoom": 16,
                },
            ]
        else:
            map_actions = [{"type": "clear_ai_layer"}]

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "unsupported_precipitation_weather",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [
                {"source": "system_capability", "scope": "air_quality_and_microclimate", "status": "unsupported_rain_sensor"}
            ] + ([{"source": "sensor", "poi_id": poi["id"], "metric": "temperature", "value": poi["temperature"], "timestamp": poi["timestamp"]}] if poi else []),
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER: General Out-of-Scope (Medical, Real Estate, Dining, Traffic)
    # -------------------------------------------------------------
    def _handle_general_out_of_scope_intent(
        self,
        q: str,
        request_id: str,
    ) -> dict[str, Any]:
        composed = ResponseComposer.compose_out_of_scope(request_id=request_id)
        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "out_of_scope",
            "evidence": [],
            "map_actions": [{"type": "clear_ai_layer"}],
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER: Specific Noise Metric
    # -------------------------------------------------------------
    def _handle_specific_noise_intent(
        self,
        poi: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        noise = poi["noise_db"]
        level_str = "rất yên tĩnh" if noise < 55 else ("mức độ âm thanh vừa phải" if noise <= 70 else "khá ồn ào")
        composed = ResponseComposer.compose_specific_noise(
            poi=poi,
            time_ctx=time_ctx,
            request_id=request_id,
        )
        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_point",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "name": poi["short_name"],
                "style": "recommended" if noise <= 60 else "caution",
            },
            {
                "type": "add_annotation",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "title": f"Độ ồn tại {poi['short_name']}",
                "subtitle": f"{noise} dB • {level_str}",
                "badge": f"{noise} dB",
                "style": "recommended" if noise <= 60 else "caution",
            },
            {"type": "fly_to", "lat": poi["latitude"], "lng": poi["longitude"], "zoom": 16},
        ]
        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "get_noise_metric",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [{"source": "sensor", "poi_id": poi["id"], "metric": "noise_db", "value": noise, "timestamp": poi["timestamp"]}],
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER: Specific Temperature Metric
    # -------------------------------------------------------------
    def _handle_specific_temp_intent(
        self,
        poi: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        temp = poi["temperature"]
        composed = ResponseComposer.compose_specific_temp(
            poi=poi,
            time_ctx=time_ctx,
            request_id=request_id,
        )
        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_point",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "name": poi["short_name"],
                "style": "recommended",
            },
            {
                "type": "add_annotation",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "title": f"Nhiệt độ: {poi['short_name']}",
                "subtitle": f"{temp}°C • AQI {poi['aqi']}",
                "badge": f"{temp}°C",
                "style": "recommended",
            },
            {"type": "fly_to", "lat": poi["latitude"], "lng": poi["longitude"], "zoom": 16},
        ]
        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "get_temperature_metric",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [{"source": "sensor", "poi_id": poi["id"], "metric": "temperature", "value": temp, "timestamp": poi["timestamp"]}],
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER: Worst Location / Most Polluted Area
    # -------------------------------------------------------------
    def _handle_worst_location_intent(
        self,
        ranked_pois: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
        mode_prefix = f"[{time_label.upper()}] " if time_ctx["is_forecast"] else ""

        # Find the POI with the highest AQI / lowest environmental quality
        worst_poi = max(ranked_pois, key=lambda p: (float(p.get("aqi", 0)), float(p.get("pm25", 0))))
        worst_sensor = worst_poi.get("sensor_id", "S01")

        # Cleaner alternative with lowest AQI
        best_poi = min(ranked_pois, key=lambda p: (float(p.get("aqi", 0)), float(p.get("pm25", 0))))
        best_sensor = best_poi.get("sensor_id", "S04")

        composed = ResponseComposer.compose_worst_location(
            worst_poi=worst_poi,
            best_poi=best_poi,
            time_ctx=time_ctx,
            request_id=request_id,
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_sensor",
                "sensor_id": worst_sensor,
                "lat": worst_poi["latitude"],
                "lng": worst_poi["longitude"],
                "severity": "danger",
            },
            {
                "type": "highlight_area",
                "area_id": worst_poi["id"],
                "name": worst_poi["short_name"],
                "lat": worst_poi["latitude"],
                "lng": worst_poi["longitude"],
                "radius_m": 300,
                "style": "avoid",
                "score": worst_poi.get("score", 30),
            },
            {
                "type": "add_annotation",
                "target_id": worst_poi["id"],
                "lat": worst_poi["latitude"],
                "lng": worst_poi["longitude"],
                "title": f"⚠️ Điểm ô nhiễm nhất: {worst_poi['short_name']}",
                "subtitle": f"{time_label} • AQI {worst_poi['aqi']} (PM2.5: {worst_poi['pm25']} µg/m³)",
                "badge": "Khu vực ô nhiễm nhất",
                "style": "danger",
            },
            {
                "type": "fly_to",
                "target_id": worst_poi["id"],
                "lat": worst_poi["latitude"],
                "lng": worst_poi["longitude"],
                "zoom": 16,
            },
        ]

        return {
            "query_type": "find_worst_location",
            "intent": "find_worst_location",
            "request_id": request_id,
            "data_mode": "forecast" if time_ctx["is_forecast"] else "live",
            "time_context": time_ctx,
            "target_station": worst_sensor,
            "target_location": worst_poi["short_name"],
            "answer": composed["answer"],
            "response": composed["response"],
            "evidence": [
                {
                    "station_id": worst_sensor,
                    "location_name": worst_poi["name"],
                    "pm25": worst_poi["pm25"],
                    "aqi": worst_poi["aqi"],
                    "score": worst_poi.get("score", 30),
                    "timestamp": worst_poi.get("timestamp"),
                    "source": "simulator",
                },
                {
                    "station_id": best_sensor,
                    "location_name": best_poi["name"],
                    "pm25": best_poi["pm25"],
                    "aqi": best_poi["aqi"],
                    "score": best_poi.get("score", 90),
                    "timestamp": best_poi.get("timestamp"),
                    "source": "simulator",
                },
            ],
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
        }

    # -------------------------------------------------------------
    # INTENT HANDLER: Explicit Indoor Activity Recommendation
    # -------------------------------------------------------------
    def _handle_explicit_indoor_intent(
        self,
        query: str,
        ranked_pois: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
        user_loc: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
        venues = spatial_registry.list_indoor_venues()

        if user_loc:
            for v in venues:
                v["dist_m"] = spatial_registry.calculate_distance_m(
                    user_loc[0], user_loc[1], v["latitude"], v["longitude"]
                )
            venues.sort(key=lambda x: x.get("dist_m", 0))

        best_v = venues[0] if venues else {
            "id": "venue_indoor_gym",
            "name": "Phòng Gym & Yoga Nội khu",
            "short_name": "Phòng Gym Nội khu",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "operating_hours": "06:00 - 22:00",
            "activities": ["Gym", "Yoga", "Chạy máy"],
            "description": "Phòng gym nội khu có hệ thống điều hòa và lọc không khí.",
        }
        alt_v = venues[1] if len(venues) > 1 else best_v

        worst_poi = ranked_pois[-1] if ranked_pois else None
        current_summary = f"AQI khu vực lên tới {worst_poi['aqi']}" if worst_poi else "chất lượng không khí ngoài trời có sự dao động"

        composed = ResponseComposer.compose_indoor_activity(
            venues=venues,
            current_summary=current_summary,
            time_ctx=time_ctx,
            request_id=request_id,
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_point",
                "target_id": best_v["id"],
                "lat": best_v["latitude"],
                "lng": best_v["longitude"],
                "name": best_v["short_name"],
                "style": "recommended",
            },
            {
                "type": "add_annotation",
                "target_id": f"{best_v['id']}_anno",
                "lat": best_v["latitude"],
                "lng": best_v["longitude"],
                "title": f"🏠 {best_v['short_name']}",
                "subtitle": f"{best_v.get('activities', ['Hoạt động trong nhà'])[0]} • Lọc khí điều hòa",
                "badge": "Vận động Trong nhà",
                "style": "recommended",
            },
            {
                "type": "highlight_point",
                "target_id": alt_v["id"],
                "lat": alt_v["latitude"],
                "lng": alt_v["longitude"],
                "name": alt_v["short_name"],
                "style": "alternative",
            },
            {
                "type": "add_annotation",
                "target_id": f"{alt_v['id']}_anno",
                "lat": alt_v["latitude"],
                "lng": alt_v["longitude"],
                "title": f"🛍️ {alt_v['short_name']}",
                "subtitle": f"{alt_v.get('activities', ['Không gian kín'])[0]}",
                "badge": "Lựa chọn trong nhà #2",
                "style": "alternative",
            },
            {
                "type": "fly_to",
                "lat": best_v["latitude"],
                "lng": best_v["longitude"],
                "zoom": 15,
            },
        ]

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "recommend_indoor_activity",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "indoor_venues": venues,
            "evidence": [
                {"source": "indoor_catalog", "venue_id": best_v["id"], "name": best_v["name"]},
                {"source": "indoor_catalog", "venue_id": alt_v["id"], "name": alt_v["name"]},
            ],
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER 1: Outdoor Recommendation (e.g. Running, Cleanest)
    # -------------------------------------------------------------
    def _handle_recommendation_intent(
        self,
        ranked_pois: list[dict[str, Any]],
        activity: str,
        time_ctx: dict[str, Any],
        request_id: str,
        user_group: str,
        user_loc: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        best = ranked_pois[0]

        # Safety evaluation: If best outdoor location is hazardous, pivot to indoor venues
        safety_eval = environmental_scoring.check_outdoor_exercise_safety(
            {
                "aqi": best["aqi"],
                "pm25": best["pm25"],
                "temperature": best["temperature"],
            },
            user_group=user_group,
        )
        if not safety_eval["safe"]:
            return self._handle_indoor_pivot_intent(
                safety_eval=safety_eval,
                user_location=user_loc,
                time_ctx=time_ctx,
                request_id=request_id,
            )

        alt = ranked_pois[1] if len(ranked_pois) > 1 else best
        worst = ranked_pois[-1]

        composed = ResponseComposer.compose_best_location(
            best_poi=best,
            alt_poi=alt,
            activity=activity,
            time_ctx=time_ctx,
            request_id=request_id,
        )

        time_label = time_ctx["label"]

        # Generate Declarative Map Actions
        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_area",
                "area_id": best["id"],
                "name": best["short_name"],
                "lat": best["latitude"],
                "lng": best["longitude"],
                "radius_m": 250,
                "style": "recommended",
                "score": best["score"],
                "rank": 1,
            },
            {
                "type": "add_annotation",
                "target_id": best["id"],
                "lat": best["latitude"],
                "lng": best["longitude"],
                "title": f"#1 Khuyến nghị: {best['short_name']}",
                "subtitle": f"{time_label} • AQI {best['aqi']} (Điểm: {best['score']})",
                "badge": "Lựa chọn tốt nhất",
                "style": "recommended",
            },
            {
                "type": "highlight_area",
                "area_id": alt["id"],
                "name": alt["short_name"],
                "lat": alt["latitude"],
                "lng": alt["longitude"],
                "radius_m": 200,
                "style": "alternative",
                "score": alt["score"],
                "rank": 2,
            },
            {
                "type": "highlight_area",
                "area_id": worst["id"],
                "name": worst["short_name"],
                "lat": worst["latitude"],
                "lng": worst["longitude"],
                "radius_m": 200,
                "style": "avoid",
                "score": worst["score"],
                "rank": len(ranked_pois),
            },
            {
                "type": "fit_bounds",
                "bounds": [
                    [min(best["latitude"], alt["latitude"]) - 0.003, min(best["longitude"], alt["longitude"]) - 0.003],
                    [max(best["latitude"], alt["latitude"]) + 0.003, max(best["longitude"], alt["longitude"]) + 0.003],
                ],
                "padding": [40, 40],
            },
        ]

        evidence = [
            {
                "source": "forecast" if time_ctx["is_forecast"] else "sensor",
                "poi_id": best["id"],
                "station_id": best["sensor_id"],
                "metric": "aqi",
                "value": best["aqi"],
                "timestamp": best["timestamp"],
            },
            {
                "source": "forecast" if time_ctx["is_forecast"] else "sensor",
                "poi_id": best["id"],
                "station_id": best["sensor_id"],
                "metric": "pm25",
                "value": best["pm25"],
                "timestamp": best["timestamp"],
            },
            {
                "source": "scoring_engine",
                "poi_id": best["id"],
                "score": best["score"],
                "activity": activity,
            },
        ]

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "recommend_outdoor_location",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": evidence,
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER: Unknown / Unrecognized Location
    # -------------------------------------------------------------
    def _handle_unknown_location_intent(
        self,
        unrecognized_loc: str,
        request_id: str,
    ) -> dict[str, Any]:
        composed = ResponseComposer.compose_unknown_location(
            unrecognized_loc=unrecognized_loc,
            request_id=request_id,
        )
        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "unknown_location",
            "unrecognized_location": unrecognized_loc,
            "evidence": [],
            "map_actions": [{"type": "clear_ai_layer"}],
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER 3: Compare Two Locations
    # -------------------------------------------------------------
    def _handle_comparison_intent(
        self,
        query: str,
        ranked_pois: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
        candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        found = []
        if candidates and len(candidates) >= 2:
            found = [next((p for p in ranked_pois if p["id"] == c["id"]), c) for c in candidates]
        else:
            mentioned = spatial_registry.find_all_pois_in_query(query)
            if len(mentioned) >= 2:
                found = [next((p for p in ranked_pois if p["id"] == m["id"]), m) for m in mentioned]
            elif len(mentioned) == 1:
                c1 = next((p for p in ranked_pois if p["id"] == mentioned[0]["id"]), mentioned[0])
                c2 = next((p for p in ranked_pois if p["id"] != c1["id"]), ranked_pois[-1])
                found = [c1, c2]

        if len(found) >= 2:
            cand_a, cand_b = found[0], found[1]
        else:
            cand_a = ranked_pois[0]
            cand_b = ranked_pois[1] if len(ranked_pois) > 1 else ranked_pois[0]

        winner = cand_a if cand_a["score"] >= cand_b["score"] else cand_b
        loser = cand_b if winner["id"] == cand_a["id"] else cand_a

        composed = ResponseComposer.compose_comparison(
            winner=winner,
            loser=loser,
            time_ctx=time_ctx,
            request_id=request_id,
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_area",
                "area_id": winner["id"],
                "target_id": winner["id"],
                "lat": winner["latitude"],
                "lng": winner["longitude"],
                "radius_m": 250,
                "name": winner["short_name"],
                "style": "recommended",
            },
            {
                "type": "add_annotation",
                "target_id": winner["id"],
                "lat": winner["latitude"],
                "lng": winner["longitude"],
                "title": f"🌿 Không khí tốt hơn: {winner['short_name']}",
                "subtitle": f"{time_ctx['label']} • AQI {winner['aqi']} (PM2.5: {winner['pm25']} µg/m³)",
                "badge": "Lựa chọn tốt hơn",
                "style": "recommended",
            },
            {
                "type": "highlight_area",
                "area_id": loser["id"],
                "target_id": loser["id"],
                "lat": loser["latitude"],
                "lng": loser["longitude"],
                "radius_m": 250,
                "name": loser["short_name"],
                "style": "caution",
            },
            {
                "type": "add_annotation",
                "target_id": loser["id"],
                "lat": loser["latitude"],
                "lng": loser["longitude"],
                "title": f"⚠️ {loser['short_name']}",
                "subtitle": f"{time_ctx['label']} • AQI {loser['aqi']} (PM2.5: {loser['pm25']} µg/m³)",
                "badge": f"Kém hơn {abs(int(winner['aqi']) - int(loser['aqi']))} AQI",
                "style": "caution",
            },
            {
                "type": "fit_bounds",
                "bounds": [
                    [min(cand_a["latitude"], cand_b["latitude"]) - 0.003, min(cand_a["longitude"], cand_b["longitude"]) - 0.003],
                    [max(cand_a["latitude"], cand_b["latitude"]) + 0.003, max(cand_a["longitude"], cand_b["longitude"]) + 0.003],
                ],
                "padding": [40, 40],
            },
        ]

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "compare_locations",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "candidates": [
                {"id": cand_a["id"], "name": cand_a["short_name"], "aqi": cand_a["aqi"], "score": cand_a["score"]},
                {"id": cand_b["id"], "name": cand_b["short_name"], "aqi": cand_b["aqi"], "score": cand_b["score"]},
            ],
            "evidence": [
                {"source": "sensor", "poi_id": cand_a["id"], "metric": "aqi", "value": cand_a["aqi"], "timestamp": cand_a["timestamp"]},
                {"source": "sensor", "poi_id": cand_b["id"], "metric": "aqi", "value": cand_b["aqi"], "timestamp": cand_b["timestamp"]},
            ],
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER 4: Single Location / Follow-up Inquiry
    # -------------------------------------------------------------
    def _handle_single_location_intent(
        self,
        poi: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
        is_interp = poi.get("is_interpolated", False)
        source_st = poi.get("source_sensors", [poi.get("sensor_id", "S01")])

        composed = ResponseComposer.compose_single_location(
            poi=poi,
            time_ctx=time_ctx,
            request_id=request_id,
        )

        if is_interp:
            evidence = [
                {
                    "source": "forecast" if time_ctx["is_forecast"] else "idw_spatial_interpolation",
                    "target_location": poi["short_name"],
                    "target_id": poi["id"],
                    "is_interpolated": True,
                    "source_sensors": source_st,
                    "metric": "aqi",
                    "value": poi["aqi"],
                    "timestamp": poi.get("timestamp"),
                },
                {
                    "source": "forecast" if time_ctx["is_forecast"] else "idw_spatial_interpolation",
                    "target_location": poi["short_name"],
                    "target_id": poi["id"],
                    "is_interpolated": True,
                    "source_sensors": source_st,
                    "metric": "pm25",
                    "value": poi["pm25"],
                    "timestamp": poi.get("timestamp"),
                },
            ]
            badge_text = f"AQI {poi['aqi']}"
        else:
            evidence = [
                {"source": "forecast" if time_ctx["is_forecast"] else "sensor", "poi_id": poi["id"], "metric": "aqi", "value": poi["aqi"], "timestamp": poi.get("timestamp")},
                {"source": "forecast" if time_ctx["is_forecast"] else "sensor", "poi_id": poi["id"], "metric": "pm25", "value": poi["pm25"], "timestamp": poi.get("timestamp")},
            ]
            badge_text = f"Điểm: {poi['score']}/100" if "score" in poi else f"AQI {poi['aqi']}"

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_area" if is_interp else "highlight_point",
                "area_id": poi["id"],
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "radius_m": 250,
                "name": poi["short_name"],
                "style": poi.get("tier", "recommended"),
            },
            {
                "type": "add_annotation",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "title": poi["short_name"],
                "subtitle": f"{time_label} • AQI {poi['aqi']} (PM2.5 {poi['pm25']} µg/m³)",
                "badge": badge_text,
                "style": poi.get("tier", "recommended"),
            },
            {
                "type": "fly_to",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "zoom": 16,
            },
        ]

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "get_location_environment",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "target_location": poi["short_name"],
            "target_station": poi.get("sensor_id"),
            "resolved_location": {
                "id": poi["id"],
                "name": poi["name"],
                "short_name": poi["short_name"],
                "category": poi.get("category", "residential"),
                "latitude": poi["latitude"],
                "longitude": poi["longitude"],
                "is_interpolated": is_interp,
                "source_sensors": source_st,
            },
            "evidence": evidence,
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER 0: Running Route Recommendation (Polyline on Map)
    # -------------------------------------------------------------
    def _handle_running_route_intent(
        self,
        ranked_routes: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
        target_distance_km: float | None = None,
        is_personalized: bool = False,
        origin_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        best = ranked_routes[0]
        alt = ranked_routes[1] if len(ranked_routes) > 1 else best

        time_label = time_ctx["label"]
        start_label = (origin_info.get("label") if origin_info else None) or best.get("start_point", {}).get("name", "Điểm xuất phát")
        composed = ResponseComposer.compose_running_route(
            best_route=best,
            origin_label=start_label,
            time_ctx=time_ctx,
            request_id=request_id,
            is_personalized=(target_distance_km is not None or is_personalized),
        )

        coords = best["coordinates"]
        lats = [c[0] for c in coords]
        lngs = [c[1] for c in coords]
        bounds = [[min(lats) - 0.002, min(lngs) - 0.002], [max(lats) + 0.002, max(lngs) + 0.002]]

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_route",
                "route_id": best["id"],
                "name": best["name"],
                "short_name": best["short_name"],
                "coordinates": best["coordinates"],
                "segments": best.get("environment_segments", []),
                "distance_km": best["distance_km"],
                "style": "recommended",
                "score": best["score"],
                "rank": 1,
                "metric": "aqi",
                "data_mode": time_ctx["type"],
                "observed_at": best.get("timestamp"),
                "source": "forecast" if time_ctx["is_forecast"] else "spatial_idw_route_segment",
            },
            {
                "type": "add_annotation",
                "target_id": f"{best['id']}_start",
                "lat": best["start_point"]["lat"],
                "lng": best["start_point"]["lng"],
                "title": f"🚩 Xuất phát: {start_label}",
                "subtitle": f"{time_label} • {best['distance_km']} km • AQI {best['aqi']} (Điểm: {best['score']})",
                "badge": "Lộ trình tối ưu #1",
                "style": "recommended",
            },
            {
                "type": "fit_bounds",
                "bounds": bounds,
                "padding": [60, 60],
            },
        ]

        evidence = [
            {
                "source": "forecast" if time_ctx["is_forecast"] else "spatial_idw_sampling",
                "route_id": best["id"],
                "metric": "mean_aqi",
                "value": best["aqi"],
                "timestamp": best.get("timestamp"),
            },
            {
                "source": "forecast" if time_ctx["is_forecast"] else "spatial_idw_sampling",
                "route_id": best["id"],
                "metric": "mean_pm25",
                "value": best["pm25"],
                "p90_aqi": best.get("p90_aqi"),
                "p90_pm25": best.get("p90_pm25"),
                "timestamp": best.get("timestamp"),
            },
            {
                "source": "route_scoring",
                "route_id": best["id"],
                "distance_km": best["distance_km"],
                "score": best["score"],
                "exposure_reduction_pct": best.get("exposure_reduction_pct", 0),
                "segment_count": best.get("segment_count", 0),
                "scoring_method": "distance_weighted_segment_exposure",
            },
        ]

        intent_name = "recommend_personalized_running_route" if (target_distance_km is not None or is_personalized) else "recommend_running_route"

        res = {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": intent_name,
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "origin": origin_info or {"source": "default_location", "lat": best["start_point"]["lat"], "lng": best["start_point"]["lng"], "label": start_label},
            "environment": best.get("environment_distribution", {}),
            "evidence": evidence,
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }
        if intent_name == "recommend_personalized_running_route":
            res["personalized_route"] = best

        return res

    # -------------------------------------------------------------
    # INTENT HANDLER -1: Indoor Activity Pivot on Hazardous Weather/Air
    # -------------------------------------------------------------
    def _handle_indoor_pivot_intent(
        self,
        safety_eval: dict[str, Any],
        user_location: tuple[float, float] | None,
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
        venues = spatial_registry.list_indoor_venues()

        # Rank indoor venues by proximity to user
        if user_location:
            for v in venues:
                v["dist_m"] = spatial_registry.calculate_distance_m(
                    user_location[0], user_location[1], v["latitude"], v["longitude"]
                )
            venues.sort(key=lambda x: x.get("dist_m", 0))

        best_v = venues[0]
        alt_v = venues[1] if len(venues) > 1 else best_v

        composed = ResponseComposer.compose_indoor_activity(
            venues=venues,
            current_summary=safety_eval.get("warning", "chất lượng không khí ngoài trời tăng cao"),
            time_ctx=time_ctx,
            request_id=request_id,
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_point",
                "target_id": best_v["id"],
                "lat": best_v["latitude"],
                "lng": best_v["longitude"],
                "name": best_v["short_name"],
                "style": "recommended",
            },
            {
                "type": "add_annotation",
                "target_id": f"{best_v['id']}_anno",
                "lat": best_v["latitude"],
                "lng": best_v["longitude"],
                "title": f"🏠 {best_v['short_name']}",
                "subtitle": f"{best_v['activities'][0]} • Lọc khí điều hòa",
                "badge": "Vận động Trong nhà",
                "style": "recommended",
            },
            {
                "type": "highlight_point",
                "target_id": alt_v["id"],
                "lat": alt_v["latitude"],
                "lng": alt_v["longitude"],
                "name": alt_v["short_name"],
                "style": "alternative",
            },
            {
                "type": "add_annotation",
                "target_id": f"{alt_v['id']}_anno",
                "lat": alt_v["latitude"],
                "lng": alt_v["longitude"],
                "title": f"🛍️ {alt_v['short_name']}",
                "subtitle": f"{alt_v['activities'][0]}",
                "badge": "Lựa chọn #2",
                "style": "alternative",
            },
            {
                "type": "fit_bounds",
                "bounds": [
                    [
                        min(best_v["latitude"], alt_v["latitude"]) - 0.003,
                        min(best_v["longitude"], alt_v["longitude"]) - 0.003,
                    ],
                    [
                        max(best_v["latitude"], alt_v["latitude"]) + 0.003,
                        max(best_v["longitude"], alt_v["longitude"]) + 0.003,
                    ],
                ],
                "padding": [60, 60],
            },
        ]

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "recommend_indoor_activity",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "safety_evaluation": safety_eval,
            "evidence": [
                {"source": "indoor_catalog", "venue_id": best_v["id"], "name": best_v["name"]},
                {"source": "indoor_catalog", "venue_id": alt_v["id"], "name": alt_v["name"]},
            ],
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER 0B: Personalized Running Route from User Origin
    # -------------------------------------------------------------
    def _handle_personalized_route_intent(
        self,
        personalized_route: dict[str, Any],
        best_base_circuit: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
        target_req = personalized_route.get("target_requested_km")
        composed = ResponseComposer.compose_running_route(
            best_route=personalized_route,
            origin_label="Vị trí của bạn",
            time_ctx=time_ctx,
            request_id=request_id,
            is_personalized=True,
        )

        coords = personalized_route["coordinates"]
        lats = [c[0] for c in coords]
        lngs = [c[1] for c in coords]
        bounds = [[min(lats) - 0.002, min(lngs) - 0.002], [max(lats) + 0.002, max(lngs) + 0.002]]

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_route",
                "route_id": personalized_route["id"],
                "name": personalized_route["name"],
                "short_name": personalized_route["short_name"],
                "coordinates": personalized_route["coordinates"],
                "distance_km": personalized_route["distance_km"],
                "style": "recommended",
                "score": personalized_route["score"],
                "rank": 1,
            },
            {
                "type": "add_annotation",
                "target_id": f"{personalized_route['id']}_user_start",
                "lat": personalized_route["start_point"]["lat"],
                "lng": personalized_route["start_point"]["lng"],
                "title": "🚩 Xuất phát từ vị trí của bạn",
                "subtitle": f"{time_label} • Cự ly {personalized_route['distance_km']} km • AQI {personalized_route['aqi']}",
                "badge": "Lộ trình Riêng",
                "style": "recommended",
            },
            {
                "type": "fit_bounds",
                "bounds": bounds,
                "padding": [60, 60],
            },
        ]

        evidence = [
            {
                "source": "personalized_routing",
                "route_id": personalized_route["id"],
                "target_km": target_req,
                "calculated_km": personalized_route["distance_km"],
                "laps": personalized_route.get("laps", 1),
            },
            {
                "source": "sensor",
                "station_id": personalized_route["sensor_id"],
                "metric": "aqi",
                "value": personalized_route["aqi"],
            },
        ]

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "recommend_personalized_running_route",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "personalized_route": personalized_route,
            "evidence": evidence,
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }


    @staticmethod
    def _usable_station_snapshot(snapshot: dict[str, Any] | None) -> bool:
        if not snapshot:
            return False
        observed_at = snapshot.get("measured_at") or snapshot.get("updated_at")
        required_metrics = ("pm25", "aqi", "co2", "noise_db", "temperature")
        return bool(
            snapshot.get("status") == "online"
            and snapshot.get("freshness") == "fresh"
            and not snapshot.get("is_stale")
            and snapshot.get("source")
            and observed_at
            and all(snapshot.get(metric) is not None for metric in required_metrics)
        )

    @staticmethod
    def _extract_explicit_station_id(query: str) -> str | None:
        """Normalize user-facing station aliases such as S1 and S01."""
        match = re.search(r"\bS0?([1-5])\b", query, flags=re.IGNORECASE)
        return f"S0{match.group(1)}" if match else None

    @staticmethod
    def _forecast_point(
        station_id: str,
        history: list[dict[str, Any]],
        forecast_hour: int,
        metric: str,
    ) -> dict[str, Any]:
        result = prophet_service.forecast(
            station_id,
            history,
            hours=max(1, forecast_hour),
            metric=metric,
        )
        horizons = result.get("horizons")
        if not isinstance(horizons, list) or not horizons:
            raise ValueError("forecast result has no horizons")
        point = horizons[-1]
        required = ("predicted_value", "timestamp", "lower_bound", "upper_bound")
        if not isinstance(point, dict) or any(point.get(field) is None for field in required):
            raise ValueError("forecast point is incomplete")
        return {
            **point,
            "source": point.get("source") or result.get("source") or result.get("model"),
        }


geospatial_agent = GeospatialAgentService()
