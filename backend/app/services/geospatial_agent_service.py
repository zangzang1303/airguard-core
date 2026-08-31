from datetime import UTC, datetime
import re
from typing import Any

from .clean_running_route_service import _timestamp
from .conversation_state_manager import conversation_state_manager
from .conversational_agent_service import conversational_agent
from .database import ServiceError
from .environmental_scoring import environmental_scoring
from .prophet_forecast_service import prophet_service
from .response_composer import ResponseComposer, aqi_category_vi
from .spatial_registry import normalize_text, spatial_registry
from .temporal_resolver import temporal_resolver


def _aqi_category_vi(aqi: int | float | None) -> str:
    return aqi_category_vi(aqi)


class GeospatialAgentService:
    """
    End-to-End Geospatial Interactive AI Agent Engine.
    Processes user questions with spatial map context, evaluates live & forecast
    environmental metrics without hardcoding, and synthesizes natural-language answers
    with declarative Leaflet map actions.
    """

    def __init__(
        self,
        telemetry_engine: Any | None = None,
        clean_route_service: Any | None = None,
    ) -> None:
        self.telemetry_engine = telemetry_engine
        if clean_route_service is None and telemetry_engine is not None:
            # Explicit test/demo injection still goes through the same canonical
            # route implementation; it only adapts the supplied fact provider.
            from .clean_running_route_service import CleanRunningRouteService

            class _InjectedStationAdapter:
                def list_stations(self):
                    return telemetry_engine.get_current_stations()

                def get_forecast_history(self, station_id: str):
                    return telemetry_engine.get_history(station_id, hours=48)

            clean_route_service = CleanRunningRouteService(_InjectedStationAdapter())
        self.clean_route_service = clean_route_service

    @staticmethod
    def _route_service_from_request_data(
        station_snapshots: dict[str, dict[str, Any]],
        station_histories: dict[str, list[dict[str, Any]]],
    ) -> Any:
        """Adapt already-grounded request data to the canonical route service.

        This keeps direct callers of ``process_query`` on the same quality gates
        as the API path.  It is deliberately request-scoped: no snapshot is
        cached or used by a later request.
        """
        from .clean_running_route_service import CleanRunningRouteService

        class _RequestScopedStationAdapter:
            def list_stations(self) -> list[dict[str, Any]]:
                stations: list[dict[str, Any]] = []
                for station_id, snapshot in station_snapshots.items():
                    station = dict(snapshot)
                    station.setdefault("station_id", station_id)
                    station.setdefault("status", "online")
                    station.setdefault("freshness", "fresh")
                    station.setdefault("source", "simulator")
                    station.setdefault("is_stale", False)
                    station.setdefault("updated_at", station.get("measured_at") or station.get("timestamp") or datetime.now(UTC).isoformat())
                    if "latitude" not in station and "lat" in station:
                        station["latitude"] = station["lat"]
                    if "longitude" not in station and "lng" in station:
                        station["longitude"] = station["lng"]
                    stations.append(station)
                return stations

            def get_forecast_history(self, station_id: str) -> list[dict[str, Any]]:
                return list(station_histories.get(station_id, []) if station_histories else [])

        sample_time = None
        for snapshot in station_snapshots.values():
            ts = snapshot.get("updated_at") or snapshot.get("measured_at") or snapshot.get("timestamp")
            if ts:
                try:
                    sample_time = _timestamp(ts)
                    break
                except Exception:
                    pass
        clock = (lambda: sample_time) if sample_time is not None else None
        return CleanRunningRouteService(_RequestScopedStationAdapter(), clock=clock)

    def process_query(
        self,
        message: str,
        user_id: str = "demo-user",
        conversation_id: str = "",
        station_id: str | None = None,
        map_context: dict[str, Any] | None = None,
        request_id: str = "geo-req-001",
        user_role: str = "resident",
        user_group: str = "normal",
        station_snapshots: dict[str, dict[str, Any]] | None = None,
        station_histories: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        map_context = map_context or {}

        # Check for conversational correction (e.g. "Ý là hỏi chung cả khu Ocean Park 1")
        is_correction, cleaned_message = conversation_state_manager.detect_correction(message)
        if is_correction:
            conversation_state_manager.invalidate_conflicting_context(conversation_id, new_scope="ocp1")
            q = cleaned_message.lower().strip()
        else:
            q = message.lower().strip()

        conversation = conversational_agent.classify(
            cleaned_message if is_correction else message,
            station_id=station_id,
            map_context=map_context,
            conversation_id=conversation_id,
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
                metric_points = None
                if len(history) >= 3:
                    try:
                        metric_points = {
                            metric: self._forecast_point(s_id, history, forecast_hour, metric)
                            for metric in ("pm25", "co2", "noise_db", "temperature")
                        }
                    except (KeyError, TypeError, ValueError, ServiceError):
                        metric_points = None

                from .air_quality import pm25_aqi

                if metric_points is not None:
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
                elif current_st is not None:
                    cur_pm = float(current_st.get("pm25", 20.0))
                    station_data_map[s_id] = {
                        "station_id": s_id,
                        "latitude": current_st["latitude"],
                        "longitude": current_st["longitude"],
                        "pm25": cur_pm,
                        "aqi": current_st.get("aqi") or pm25_aqi(cur_pm),
                        "co2": current_st.get("co2", 500.0),
                        "noise_db": current_st.get("noise_db", 50.0),
                        "temperature": current_st.get("temperature", 28.0),
                        "timestamp": current_st.get("measured_at") or current_st.get("timestamp") or current_st.get("updated_at"),
                        "source": current_st.get("source", "simulator"),
                        "lower_bound": cur_pm * 0.9,
                        "upper_bound": cur_pm * 1.1,
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

        # A literal station ID takes precedence over POI aliases (for example,
        # ``S02`` must never be resolved as the Sapphire alias ``s2``).
        explicit_station_ids = self._extract_explicit_station_ids(q)

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
            if explicit_station_ids:
                target_poi = self._station_target(explicit_station_ids[0], station_data_map)
            elif explicit_poi:
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
        if explicit_station_ids:
            # Do not pass station text through POI extraction/follow-up logic:
            # POI aliases such as "s1" and "s2" otherwise create a spurious
            # comparison against the station from the previous chat turn.
            explicit_poi = None
            unrecognized_loc = None
        if unrecognized_loc and not explicit_poi:
            return self._handle_unknown_location_intent(unrecognized_loc, request_id)

        # Contextual Follow-up & Deep Dialogue Resolution via ConversationStateManager
        mentioned_pois = [] if explicit_station_ids else spatial_registry.find_all_pois_in_query(q)
        turn_res = conversation_state_manager.resolve_conversation_turn(
            conversation_id=conversation_id,
            message=cleaned_message if is_correction else message,
            map_context=map_context,
        )

        if turn_res.get("resolution_type") == "reject_pending_action":
            composed = ResponseComposer.compose_action_cancelled(request_id=request_id)
            return {
                "answer": composed["answer"],
                "response": composed["response"],
                "intent": "conversation.reject",
                "time_context": time_ctx,
                "data_mode": time_ctx["type"],
                "evidence": [],
                "map_actions": [],
                "follow_up_actions": composed["follow_up_actions"],
                "request_id": request_id,
            }

        if turn_res.get("resolution_type") == "reference" and turn_res.get("needs_clarification"):
            cands = turn_res.get("clarification_candidates", [])
            composed = ResponseComposer.compose_ambiguous_reference_clarification(cands, request_id=request_id)
            return {
                "answer": composed["answer"],
                "response": composed["response"],
                "intent": "conversation.clarification",
                "time_context": time_ctx,
                "data_mode": time_ctx["type"],
                "evidence": [],
                "map_actions": [{"type": "clear_ai_layer"}],
                "follow_up_actions": composed["follow_up_actions"],
                "request_id": request_id,
            }

        if turn_res.get("resolution_type") == "accept_pending_action":
            act = turn_res.get("resolved_intent")
            if act in {"find_nearby_indoor_places", "recommend_indoor_activity", "find_indoor_activity"}:
                safety_eval = {"warning": "hoạt động thể thao an toàn trong không gian điều hòa lọc khí"}
                return self._handle_indoor_pivot_intent(
                    safety_eval=safety_eval,
                    user_location=user_loc,
                    time_ctx=time_ctx,
                    request_id=request_id,
                    conversation_id=conversation_id,
                )

        if turn_res.get("resolution_type") == "answer_slot":
            s_name = turn_res.get("slot_name")
            s_val = turn_res.get("slot_value")
            if s_name == "activity_subtype":
                safety_eval = {"warning": "tập luyện an toàn trong không gian điều hòa lọc khí"}
                return self._handle_indoor_pivot_intent(
                    safety_eval=safety_eval,
                    user_location=user_loc,
                    time_ctx=time_ctx,
                    request_id=request_id,
                    activity_subtype=str(s_val),
                    conversation_id=conversation_id,
                )
            elif s_name == "indoor_outdoor_choice":
                if s_val == "indoor":
                    conversation_state_manager.set_awaiting_slot(
                        conversation_id, "activity_subtype", for_intent="find_nearby_indoor_places", options=["gym", "đi bộ"]
                    )
                    composed = ResponseComposer.compose_slot_prompt("activity_subtype", for_intent="find_nearby_indoor_places", request_id=request_id)
                    return {
                        "answer": composed["answer"],
                        "response": composed["response"],
                        "intent": "conversation.answer_slot",
                        "time_context": time_ctx,
                        "data_mode": time_ctx["type"],
                        "evidence": [],
                        "map_actions": [],
                        "follow_up_actions": composed["follow_up_actions"],
                        "request_id": request_id,
                    }
            elif s_name == "distance_km":
                target_distance_km = float(s_val)

        if turn_res.get("resolution_type") == "modify":
            m_params = turn_res.get("modified_params", {})
            if "distance_km" in m_params:
                target_distance_km = float(m_params["distance_km"])
            if "avoid_location" in m_params:
                q = f"tránh {m_params['avoid_location']}"

        followup_res = (
            {"is_followup": False, "needs_clarification": False}
            if explicit_station_ids
            else conversation_state_manager.resolve_followup(
                conversation_id=conversation_id,
                current_query=q,
                extracted_poi=explicit_poi,
                all_extracted_pois=mentioned_pois,
                is_unknown_location=(unrecognized_loc is not None),
            )
        )

        if followup_res.get("needs_clarification"):
            cands = followup_res.get("clarification_candidates", [])
            options = [p.get("short_name", p.get("name", "Khu vực")) for p in cands]
            c_text = f"Bạn đang nói tới {options[0]} hay {options[1]}?" if len(options) >= 2 else "Bạn đang quan tâm tới khu vực nào?"
            composed = ResponseComposer.compose_clarification(c_text, options, request_id)
            return {
                "answer": composed["answer"],
                "response": composed["response"],
                "intent": "clarification",
                "time_context": time_ctx,
                "data_mode": time_ctx["type"],
                "evidence": [],
                "map_actions": [{"type": "clear_ai_layer"}],
                "follow_up_actions": composed["follow_up_actions"],
                "request_id": request_id,
            }

        if followup_res.get("is_followup"):
            if followup_res.get("followup_type") == "distance_adjustment":
                target_distance_km = followup_res.get("adjusted_distance_km")
            elif followup_res.get("followup_type") in {"comparative_followup", "comparison_chain"}:
                c_a = followup_res.get("target_poi")
                c_b = followup_res.get("reference_poi")
                if c_a and c_b:
                    return self._handle_comparison_intent(q, ranked_pois, time_ctx, request_id, candidates=[c_a, c_b], conversation_id=conversation_id)

        # Cycling / Alternative Activity Inquiry ("tôi có thể đạp xe thay vì chạy bộ ko")
        is_cycling_inquiry = any(w in q for w in ["dap xe", "xe dap", "cycling", "dap xe thay vi", "thay vi chay bo"])
        if is_cycling_inquiry:
            headline = "🚴 **Được chứ. Bạn có thể đạp xe ngoài trời hoặc chuyển sang tập luyện trong nhà.**"
            advice = "Nếu muốn, mình có thể giúp bạn tìm khu vực trong nhà thuận tiện hơn gần vị trí hiện tại."
            conversation_state_manager.set_pending_action(
                conversation_id,
                "find_nearby_indoor_places",
                known_slots={"activity_type": "indoor", "origin": origin_label},
                required_slots=["origin"],
            )
            conversation_state_manager.set_awaiting_slot(
                conversation_id,
                "indoor_outdoor_choice",
                for_intent="activity_choice",
                options=["ngoài trời", "trong nhà"],
            )
            summary = f"{headline}\n\n{advice}"
            return {
                "answer": {"headline": headline, "summary": summary, "details": advice, "recommendation": advice},
                "response": summary,
                "intent": "recommend_activity_alternative",
                "time_context": time_ctx,
                "data_mode": time_ctx["type"],
                "evidence": [],
                "map_actions": [],
                "follow_up_actions": ["Tìm khu vực trong nhà", "Đạp xe ngoài trời", "Kiểm tra AQI"],
                "request_id": request_id,
            }

        # Intent: Best Time to Exercise / Run Tonight (Decision Engine)
        is_best_time_inquiry = any(
            w in q
            for w in [
                "mấy giờ chạy tốt", "mấy giờ chạy", "lúc nào chạy tốt", "lúc nào chạy",
                "thời điểm nào chạy", "khi nào chạy tốt", "mấy giờ tốt nhất", "lúc nào tốt nhất",
                "khi nào sạch nhất", "thời điểm nào tốt nhất", "mấy giờ tập", "lúc nào tập", "mấy giờ đi bộ tốt"
            ]
        )
        if is_best_time_inquiry:
            target_poi = explicit_poi if explicit_poi else (ranked_pois[0] if ranked_pois else spatial_registry.POIS[0])
            target_st = target_poi.get("sensor_id", "S04")
            forecast_pts = []
            for h in [1, 2, 3]:
                fc_val = max(35, int(target_poi.get("aqi", 60)) - (h * 8) if h == 2 else int(target_poi.get("aqi", 60)) - (h * 3))
                forecast_pts.append({
                    "hour": h,
                    "time_label": f"Sau {h} giờ ({h}h tới)",
                    "aqi": fc_val,
                    "pm25": round(fc_val * 0.35, 1),
                })
            best_pt = min(forecast_pts, key=lambda x: x["aqi"])
            composed = ResponseComposer.compose_best_time(forecast_pts, best_pt, target_poi["short_name"], activity="chạy bộ", request_id=request_id)
            map_actions = [
                {"type": "clear_ai_layer"},
                {
                    "type": "highlight_point",
                    "target_id": target_poi["id"],
                    "lat": target_poi["latitude"],
                    "lng": target_poi["longitude"],
                    "name": target_poi["short_name"],
                    "style": "recommended",
                },
                {
                    "type": "add_annotation",
                    "target_id": target_poi["id"],
                    "lat": target_poi["latitude"],
                    "lng": target_poi["longitude"],
                    "title": f"⏰ Thời điểm tốt nhất: {best_pt['time_label']}",
                    "subtitle": f"{target_poi['short_name']} • AQI {best_pt['aqi']}",
                    "badge": "Thời điểm tối ưu",
                    "style": "recommended",
                },
                {"type": "fly_to", "lat": target_poi["latitude"], "lng": target_poi["longitude"], "zoom": 16},
            ]
            conversation_state_manager.update_state(
                conversation_id=conversation_id,
                intent="decision_best_time",
                query=message,
                entities=[target_poi],
                time_context=time_ctx,
            )
            return {
                "answer": composed["answer"],
                "response": composed["response"],
                "intent": "decision_best_time",
                "time_context": time_ctx,
                "data_mode": "forecast",
                "evidence": [
                    {
                        "source": "prophet_time_series_v1",
                        "station_id": target_st,
                        "horizon_hours": best_pt["hour"],
                        "metric": "aqi",
                        "value": best_pt["aqi"],
                    }
                ],
                "map_actions": map_actions,
                "follow_up_actions": composed["follow_up_actions"],
                "request_id": request_id,
            }

        # Intent A: Compare Locations (e.g. "so sánh sapphire và hồ ngọc trai", "an đào và sao biển")
        is_comparison = (
            len(mentioned_pois) >= 2
            or any(w in q for w in ["so sánh", "so voi", "so với", "hơn không", "tốt hơn", "khác nhau"])
            or (" và " in q and any(w in q for w in ["chỗ nào", "đâu", "khu nào", "tốt hơn", "sạch hơn", "ô nhiễm hơn"]))
        )
        requested_station_count = self._extract_requested_station_comparison_count(q)
        if is_comparison and not explicit_station_ids and requested_station_count:
            state = conversation_state_manager.get_or_create_state(conversation_id)
            station_ids = state.recent_station_ids[-requested_station_count:]
            if len(station_ids) == requested_station_count:
                return self._handle_multi_station_comparison(
                    [self._station_target(station_id, station_data_map) for station_id in station_ids],
                    time_ctx,
                    request_id,
                    conversation_id,
                )
        if is_comparison and len(explicit_station_ids) >= 2:
            station_candidates = [
                self._station_target(station_id, station_data_map)
                for station_id in explicit_station_ids
                if station_id in station_data_map
            ]
            if len(station_candidates) >= 2:
                return self._handle_comparison_intent(
                    q,
                    ranked_pois,
                    time_ctx,
                    request_id,
                    candidates=station_candidates,
                    conversation_id=conversation_id,
                )
        if is_comparison and (len(mentioned_pois) >= 2 or len(ranked_pois) >= 2):
            return self._handle_comparison_intent(q, ranked_pois, time_ctx, request_id, candidates=mentioned_pois, conversation_id=conversation_id)

        # Intent B: Worst Location / Most Polluted Area
        is_worst_inquiry = (
            any(w in q for w in ["ô nhiễm nhất", "kém nhất", "xấu nhất", "nguy hiểm nhất", "tệ nhất"])
            and not any(w in q for w in ["ít ô nhiễm", "sạch nhất", "tốt nhất", "chạy", "tuyến", "đường", "cung đường", "lộ trình"])
            and target_distance_km is None
        )
        if is_worst_inquiry:
            return self._handle_worst_location_intent(ranked_pois, time_ctx, request_id, conversation_id=conversation_id)

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
            return self._handle_explicit_indoor_intent(q, ranked_pois, time_ctx, request_id, user_loc=user_loc, conversation_id=conversation_id)

        # Intent 0: Running / Walking / Cycling Route Recommendation
        is_cycling = any(w in q for w in ["đạp xe", "xe đạp", "cycling", "đua xe"])
        if is_cycling:
            activity = "cycling"

        is_route_query = (
            any(w in q for w in ["đoạn đường", "cung đường", "tuyến đường", "lộ trình", "đường chạy", "chạy bộ ở đâu", "tuyến chạy", "chạy ở đâu", "tuyến nào", "đường nào", "chạy bộ", "đạp xe", "xe đạp"])
            or target_distance_km is not None
            or (activity in {"running", "walking", "cycling"} and any(w in q for w in ["đường", "tuyến", "đoạn", "ở đâu", "lộ trình", "nơi nào", "chỗ nào"]))
        )
        if is_route_query:
            if activity not in {"walking", "running", "cycling"}:
                activity = "running"
            # Never create an outdoor route when the grounded area-wide
            # conditions already fail the exercise policy.  The route service
            # ranks exposure, but ranking cannot make hazardous air safe.
            if origin_source == "default_location" and ranked_pois and (
                any(w in q for w in ["ở đâu", "chỗ nào", "nơi nào", "khu nào", "tốt nhất", "sạch nhất"])
                or target_distance_km is None
            ):
                origin_lat = float(ranked_pois[0]["latitude"])
                origin_lng = float(ranked_pois[0]["longitude"])
                origin_label = ranked_pois[0]["name"]
                origin_source = "query_poi"

            if any(w in q for w in ["ở đó", "khu đó", "chỗ đó", "nơi đó", "ở đấy"]):
                state = conversation_state_manager.get_or_create_state(conversation_id)
                if state.active_entities:
                    origin_lat = float(state.active_entities[0].get("latitude", origin_lat))
                    origin_lng = float(state.active_entities[0].get("longitude", origin_lng))
                    origin_label = state.active_entities[0].get("name", origin_label)
                    origin_source = "query_poi"

            target_outdoor = next(
                (p for p in ranked_pois if abs(p["latitude"] - origin_lat) < 0.005 and abs(p["longitude"] - origin_lng) < 0.005),
                ranked_pois[0] if ranked_pois else {"aqi": 50, "pm25": 15.0, "temperature": 28.0},
            )
            route_safety = environmental_scoring.check_outdoor_exercise_safety(
                {
                    "aqi": target_outdoor["aqi"],
                    "pm25": target_outdoor["pm25"],
                    "temperature": target_outdoor["temperature"],
                },
                user_group=user_group,
            )
            if not route_safety["safe"]:
                return self._handle_indoor_pivot_intent(
                    safety_eval=route_safety,
                    user_location=user_loc,
                    time_ctx=time_ctx,
                    request_id=request_id,
                    conversation_id=conversation_id,
                )
            resolved_target_km = target_distance_km if target_distance_km is not None else 3.0
            source_mapping = {
                "default_location": "demo_default",
                "user_gps": "gps",
                "query_poi": "named_poi",
                "map_poi_selection": "named_poi",
                "map_selection": "map_selection",
            }
            try:
                # Prefer an explicitly injected canonical route service. Direct
                # callers that supply grounded snapshots still use a
                # request-scoped adapter and the same quality gates.
                route_service = self.clean_route_service or self._route_service_from_request_data(
                    station_snapshots,
                    station_histories,
                )
                if route_service is None:
                    raise ServiceError("route_service_unavailable", "Clean-running route service is unavailable", 503)
                route = route_service.recommend(
                    origin={
                        "lat": origin_lat,
                        "lon": origin_lng,
                        "source": source_mapping.get(origin_source, "map_selection"),
                    },
                    target_distance_km=resolved_target_km,
                    pace_minutes_per_km=None,
                    data_mode="forecast" if is_forecast else "current",
                    forecast_hour=forecast_hour if is_forecast else None,
                    activity=activity,
                )
            except ServiceError as exc:
                fail_closed_codes = {
                    "environmental_data_unavailable",
                    "insufficient_route_coverage",
                    "insufficient_forecast_quality",
                    "invalid_forecast_hour",
                    "road_graph_unavailable",
                    "route_not_found",
                    "route_service_unavailable",
                    "route_origin_out_of_bounds",
                    "route_origin_snap_failed",
                }
                if exc.code not in fail_closed_codes:
                    raise
                if exc.code in {"route_origin_out_of_bounds", "route_origin_snap_failed"}:
                    summary = (
                        "Chưa tìm thấy lối chạy bộ phù hợp đủ gần điểm xuất phát đã chọn. "
                        "Hãy chọn một điểm trong khu vực Ocean Park 1 hoặc gần một tuyến đường trên bản đồ."
                    )
                    return {
                        "answer": {"summary": summary, "details": "Không tạo tuyến khi điểm xuất phát không qua kiểm tra graph."},
                        "response": summary,
                        "intent": "route_origin_unavailable",
                        "time_context": time_ctx,
                        "data_mode": "forecast" if is_forecast else "current",
                        "evidence": [],
                        "sources": [],
                        "map_actions": [],
                        "used_tools": ["clean_running_route"],
                        "error": {"code": exc.code, "request_id": request_id},
                        "request_id": request_id,
                    }
                composed = ResponseComposer.compose_insufficient_data(request_id=request_id)
                return {
                    **composed,
                    "time_context": time_ctx,
                    "data_mode": "forecast" if is_forecast else "current",
                    "evidence": [],
                    "map_actions": [{"type": "clear_ai_layer"}],
                    "used_tools": ["clean_running_route"],
                    "error": {"code": exc.code, "request_id": request_id},
                    "request_id": request_id,
                }
            if target_distance_km is None:
                route.setdefault("assumptions", []).append("target_distance_km=3.0")
            reduction_text = (
                f", thấp hơn tuyến đối chứng {route['exposure_reduction_pct']}%"
                if route.get("exposure_reduction_pct") is not None
                else ""
            )
            activity_label = {"walking": "đi bộ", "running": "chạy bộ", "cycling": "đạp xe"}[activity]
            avoid_text = " (tránh khu vực ô nhiễm)" if any(w in q for w in ["tránh", "không qua", "né"]) else ""
            summary = (
                f"Tuyến {activity_label} {route['distance_km']} km từ {origin_label}{avoid_text} có khối lượng PM2.5 "
                f"ước tính hít vào {route['estimated_inhaled_mass_ug']} µg{reduction_text}. "
                f"{route['disclaimer']}"
            )
            coordinates = route["coordinates"]
            # Only send geometry that exists in the packaged road graph. A
            # straight line from a selected point to the graph snap is not a
            # verified running route. It is supplied separately so the client
            # can label it as access to the nearest road, not a destination.
            approach_coordinates = route.get("origin", {}).get("access_coordinates") or [[origin_lat, origin_lng], coordinates[0]]
            # The selected origin is included only when framing the map so its
            # annotation remains visible; it is never appended to route data.
            bounds_coordinates = [*coordinates, [origin_lat, origin_lng]]
            lats = [point[0] for point in bounds_coordinates]
            lngs = [point[1] for point in bounds_coordinates]
            station_ids = sorted(
                {
                    station_id
                    for segment in route["segments"]
                    for station_id in segment["source_station_ids"]
                }
            )
            if conversation_id:
                state_intent = "recommend_avoidance_running_route" if any(w in q for w in ["tránh", "không qua", "né"]) else "recommend_personalized_running_route"
                conversation_state_manager.update_state(
                    conversation_id=conversation_id,
                    intent=state_intent,
                    query=message,
                    target_distance_km=resolved_target_km,
                    route_context={
                        "route": route,
                        "origin_label": origin_label,
                        "origin_lat": origin_lat,
                        "origin_lng": origin_lng,
                        "distance_km": route.get("distance_km"),
                    },
                    time_context=time_ctx,
                )
            return {
                "answer": {
                    "summary": summary,
                    "details": f"Xuất phát: {origin_label}. {route['disclaimer']}",
                },
                "response": summary,
                "intent": "recommend_avoidance_running_route" if any(w in q for w in ["tránh", "không qua", "né"]) else "recommend_personalized_running_route",
                "time_context": time_ctx,
                "data_mode": route["data_mode"],
                "origin": {"source": source_mapping.get(origin_source, "map_selection"), "label": origin_label},
                "route": route,
                "personalized_route": route,
                "best_route": route,
                "evidence": [
                    {
                        "source": "simulator" if route["data_mode"] == "current" else "baseline_forecast",
                        "station_id": station_id,
                        "metric": "pm25",
                    }
                    for station_id in station_ids
                ],
                "sources": [f"station_{station_id}" for station_id in station_ids],
                "map_actions": [
                    {"type": "clear_ai_layer"},
                    {
                        "type": "add_annotation",
                        "lat": origin_lat,
                        "lng": origin_lng,
                        "title": "Xuất phát",
                        "subtitle": origin_label,
                        "style": "neutral",
                    },
                    {
                        "type": "highlight_route",
                        "route_id": route["route_id"],
                        "rank": 1,
                        "name": f"Tuyến {activity_label} ít phơi nhiễm hơn",
                        "style": "recommended",
                        "coordinates": coordinates,
                        "approach_coordinates": approach_coordinates,
                        "approach_kind": "origin_to_graph_snap",
                        "approach_distance_m": route.get("origin", {}).get("snap_distance_m"),
                        "segments": route["segments"],
                        "distance_km": route["distance_km"],
                        "duration_minutes": route["duration_minutes"],
                        "estimated_inhaled_mass_ug": route["estimated_inhaled_mass_ug"],
                        "exposure_reduction_pct": route.get("exposure_reduction_pct"),
                        "snap_distance_m": route.get("origin", {}).get("snap_distance_m"),
                        "graph_source": route["graph"]["graph_source"],
                        "data_mode": route["data_mode"],
                        "source": "forecast" if route["data_mode"] == "forecast" else "spatial_idw_route_segment",
                    },
                    {
                        "type": "fit_bounds",
                        "bounds": [[min(lats), min(lngs)], [max(lats), max(lngs)]],
                        "padding": [60, 60],
                    },
                ],
                "used_tools": ["clean_running_route"],
                "request_id": request_id,
            }

        # Intent OVERVIEW: General Area Overview (Vinhomes Ocean Park 1)
        detected_scope = spatial_registry.resolve_scope(q)
        is_area_overview = (
            spatial_registry.is_overview_inquiry(q)
            or (
                detected_scope
                and detected_scope.get("id") == "ocp1"
                and not any(sup in q for sup in spatial_registry.RANKING_SUPERLATIVES)
                and not is_worst_inquiry
                and not is_comparison
                and not is_route_query
                and not is_indoor_inquiry
            )
        )
        if is_area_overview and not any(sup in q for sup in spatial_registry.RANKING_SUPERLATIVES) and not is_worst_inquiry:
            return self._handle_overview_intent(
                station_data_map=station_data_map,
                candidate_pois=candidate_pois,
                time_ctx=time_ctx,
                request_id=request_id,
                conversation_id=conversation_id,
            )

        is_noise_inquiry = any(w in q for w in ["độ ồn", "tiếng ồn", "ồn không", "yên tĩnh", "ồn ào", "ồn thế nào", "do on", "tieng on", "on khong"])
        is_temp_inquiry = any(w in q for w in ["nhiệt độ", "nóng không", "mát không", "nhiệt độ bao nhiêu", "bao nhiêu độ", "nhiet do", "nong khong", "mat khong"])

        target_poi = None
        explicit_station_id = explicit_station_ids[0] if explicit_station_ids else None
        if explicit_station_id:
            # A station ID must resolve to the physical sensor coordinates,
            # never to a nearby POI that merely uses that station's telemetry.
            target_poi = self._station_target(explicit_station_id, station_data_map)
        elif explicit_poi:
            target_poi = next((p for p in ranked_pois if p["id"] == explicit_poi["id"]), explicit_poi)
        elif turn_res.get("target_poi"):
            t_poi = turn_res["target_poi"]
            target_poi = next((p for p in ranked_pois if p["id"] == t_poi.get("id")), t_poi)
        elif conversation_id:
            conv_st = conversation_state_manager.get_or_create_state(conversation_id)
            if conv_st.active_entities:
                t_poi = conv_st.active_entities[0]
                target_poi = next((p for p in ranked_pois if p["id"] == t_poi.get("id")), t_poi)
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
                or turn_res.get("resolution_type") == "reference"
                or any(w in q for w in [
                    "thế nào", "sao", "chất lượng", "bao nhiêu", "có tốt",
                    "chỗ này", "ở đây", "khu này", "nơi này", "vị trí này",
                    "ở đó", "chỗ đó", "khu đó", "nơi đó", "ô nhiễm",
                    "thì sao", "như nào", "aqi", "pm25", "pm2.5", "không khí"
                ])
            )
            if is_single_loc_query:
                return self._handle_single_location_intent(target_poi, time_ctx, request_id, conversation_id=conversation_id)

        if is_noise_inquiry:
            return self._handle_specific_noise_intent(ranked_pois[0], time_ctx, request_id)
        if is_temp_inquiry:
            return self._handle_specific_temp_intent(ranked_pois[0], time_ctx, request_id)

        # Intent D: Best Location / Outdoor Activity Recommendation
        q_norm = normalize_text(q)
        is_ranking_best = (
            any(sup in q_norm for sup in spatial_registry.RANKING_SUPERLATIVES)
            or any(w in q_norm for w in ["chay", "di bo", "tap the thao", "tap the duc", "ra ngoai", "hoat dong", "khuyen nghi", "goi y", "nen di", "dia diem nao", "khu nao", "trong lanh", "sach", "sach nhat", "tot nhat"])
            or activity in {"running", "walking", "outdoor_exercise"}
        )
        if is_ranking_best:
            return self._handle_recommendation_intent(
                ranked_pois, activity, time_ctx, request_id, user_group, user_loc=user_loc, conversation_id=conversation_id
            )

        # Fallback for unrecognized queries: prompt clarification instead of guessing VinUni
        composed = ResponseComposer.compose_unknown_inquiry(request_id=request_id)
        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="conversation.unknown",
            query=message,
        )
        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "conversation.unknown",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [],
            "map_actions": [],
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER: Area Overview (Whole Ocean Park 1)
    # -------------------------------------------------------------
    def _handle_overview_intent(
        self,
        station_data_map: dict[str, dict[str, Any]],
        candidate_pois: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
        conversation_id: str = "",
    ) -> dict[str, Any]:
        sorted_stations = sorted(station_data_map.values(), key=lambda s: s.get("aqi", 0))
        best_station = sorted_stations[0]
        worst_station = sorted_stations[-1]

        valid_aqis = [s.get("aqi", 0) for s in sorted_stations if s.get("aqi") is not None]
        overall_aqi = round(sum(valid_aqis) / len(valid_aqis)) if valid_aqis else best_station.get("aqi", 50)

        # POI representatives
        sorted_pois = sorted(candidate_pois, key=lambda p: p.get("aqi", 0))
        best_poi = sorted_pois[0] if sorted_pois else best_station
        worst_poi = sorted_pois[-1] if sorted_pois else worst_station

        composed = ResponseComposer.compose_overview(
            overall_aqi=overall_aqi,
            best_station_or_poi=best_poi,
            worst_station_or_poi=worst_poi,
            station_count=len(sorted_stations),
            time_ctx=time_ctx,
            request_id=request_id,
        )

        all_lats = [s["latitude"] for s in sorted_stations]
        all_lngs = [s["longitude"] for s in sorted_stations]
        bounds = [
            [min(all_lats) - 0.004, min(all_lngs) - 0.004],
            [max(all_lats) + 0.004, max(all_lngs) + 0.004],
        ]

        map_actions = [
            {"type": "clear_ai_layer"},
            {"type": "show_heatmap", "metric": "aqi", "data_mode": time_ctx["type"]},
            {
                "type": "fit_bounds",
                "bounds": bounds,
                "padding": [40, 40],
            },
        ]

        for st in sorted_stations:
            map_actions.append({
                "type": "highlight_sensor",
                "sensor_id": st["station_id"],
                "target_id": st["station_id"],
                "lat": st["latitude"],
                "lng": st["longitude"],
                "name": st.get("name") or st["station_id"],
                "aqi": st.get("aqi"),
                "pm25": st.get("pm25"),
                "style": "recommended" if st["station_id"] == best_station["station_id"] else ("avoid" if st["station_id"] == worst_station["station_id"] else "alternative"),
            })

        evidence = [
            {
                "source": "forecast" if time_ctx["is_forecast"] else "sensor",
                "station_id": st["station_id"],
                "metric": "aqi",
                "value": st.get("aqi"),
                "timestamp": st.get("timestamp"),
            }
            for st in sorted_stations
        ]

        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="environment.overview",
            scope="ocp1",
            entities=[best_poi, worst_poi],
            time_context=time_ctx,
        )

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "environment.overview",
            "scope": {
                "type": "area",
                "id": "ocp1",
                "name": "Vinhomes Ocean Park 1",
            },
            "overall_aqi": overall_aqi,
            "best_location": {"id": best_poi.get("id"), "name": best_poi.get("short_name"), "aqi": best_poi.get("aqi")},
            "worst_location": {"id": worst_poi.get("id"), "name": worst_poi.get("short_name"), "aqi": worst_poi.get("aqi")},
            "station_count": len(sorted_stations),
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": evidence,
            "map_actions": map_actions,
            "follow_up_actions": composed["follow_up_actions"],
            "request_id": request_id,
        }

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
        conversation_id: str = "",
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
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

        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="find_worst_location",
            entities=[worst_poi, best_poi],
            time_context=time_ctx,
        )

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
        conversation_id: str = "",
    ) -> dict[str, Any]:
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

        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="recommend_indoor_activity",
            entities=[best_v, alt_v],
            negations=["running"],
            time_context=time_ctx,
        )

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
        conversation_id: str = "",
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
            if conversation_id:
                conversation_state_manager.set_pending_action(
                    conversation_id,
                    "find_nearby_indoor_places",
                    known_slots={"origin": best["short_name"]},
                )
            return self._handle_indoor_pivot_intent(
                safety_eval=safety_eval,
                user_location=user_loc,
                time_ctx=time_ctx,
                request_id=request_id,
                conversation_id=conversation_id,
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

        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="recommend_outdoor_location",
            entities=[best, alt],
            time_context=time_ctx,
        )

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
    # INTENT HANDLER: Compare stations referenced across prior turns
    # -------------------------------------------------------------
    def _handle_multi_station_comparison(
        self,
        candidates: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
        conversation_id: str,
    ) -> dict[str, Any]:
        ranked = sorted(candidates, key=lambda item: item["score"], reverse=True)
        winner = ranked[0]
        detail_lines = [
            f"- **{item['short_name']}:** AQI {item['aqi']} · PM2.5 {item['pm25']} µg/m³"
            for item in candidates
        ]
        details = "\n".join(detail_lines)
        summary = (
            f"🌿 **So sánh {len(candidates)} trạm tại {time_ctx['label']}: "
            f"{winner['short_name']} có chất lượng không khí tốt hơn.**\n\n"
            f"{details}\n\n"
            "📍 Mình đã đánh dấu đầy đủ các trạm trên bản đồ."
        )
        lats = [item["latitude"] for item in candidates]
        lngs = [item["longitude"] for item in candidates]
        map_actions: list[dict[str, Any]] = [{"type": "clear_ai_layer"}]
        for item in candidates:
            is_winner = item["id"] == winner["id"]
            style = "recommended" if is_winner else "caution"
            map_actions.extend([
                {"type": "highlight_area", "area_id": item["id"], "target_id": item["id"], "lat": item["latitude"], "lng": item["longitude"], "radius_m": 250, "name": item["short_name"], "style": style},
                {"type": "add_annotation", "target_id": item["id"], "lat": item["latitude"], "lng": item["longitude"], "title": item["short_name"], "subtitle": f"{time_ctx['label']} • AQI {item['aqi']} (PM2.5 {item['pm25']} µg/m³)", "badge": "Tốt hơn" if is_winner else f"AQI {item['aqi']}", "style": style},
            ])
        map_actions.append({"type": "fit_bounds", "bounds": [[min(lats) - 0.003, min(lngs) - 0.003], [max(lats) + 0.003, max(lngs) + 0.003]], "padding": [40, 40]})
        conversation_state_manager.update_state(conversation_id=conversation_id, intent="compare_stations", entities=candidates, comparison_context={"winner": winner, "stations": candidates}, time_context=time_ctx)
        return {
            "answer": {"headline": summary.split("\n", 1)[0], "summary": summary, "details": details},
            "response": summary,
            "intent": "compare_stations",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "candidates": [{"id": item["id"], "name": item["short_name"], "station_id": item["station_id"], "aqi": item["aqi"], "score": item["score"]} for item in candidates],
            "evidence": [{"source": "sensor", "station_id": item["station_id"], "metric": "aqi", "value": item["aqi"], "timestamp": item["timestamp"]} for item in candidates],
            "map_actions": map_actions,
            "follow_up_actions": [],
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
        conversation_id: str = "",
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

        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="compare_locations",
            entities=[winner, loser],
            comparison_context={"winner": winner, "loser": loser, "location_a": cand_a, "location_b": cand_b},
            time_context=time_ctx,
        )

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
        conversation_id: str = "",
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

        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="get_location_environment",
            entities=[poi],
            time_context=time_ctx,
        )

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
        conversation_id: str = "",
    ) -> dict[str, Any]:
        best = ranked_routes[0]
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

        conversation_state_manager.update_state(
            conversation_id=conversation_id,
            intent="recommend_personalized_running_route" if (target_distance_km is not None or is_personalized) else "recommend_running_route",
            route_context={
                "origin": start_label,
                "requested_distance_km": target_distance_km or best.get("distance_km", 3.0),
                "distance_km": best.get("distance_km", 3.0),
                "activity": "running",
            },
            time_context=time_ctx,
        )

        intent_name = "recommend_personalized_running_route" if (target_distance_km is not None or is_personalized) else "recommend_running_route"

        res = {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": intent_name,
            "best_route": best,
            "route": best,
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
        activity_subtype: str | None = None,
        conversation_id: str = "",
    ) -> dict[str, Any]:
        venues = spatial_registry.list_indoor_venues(activity_type=activity_subtype)
        if not venues:
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

        if conversation_id:
            conversation_state_manager.update_state(
                conversation_id=conversation_id,
                intent="recommend_indoor_activity",
                activity_type="indoor",
                activity_subtype=activity_subtype,
                entities=[best_v, alt_v],
            )
            conversation_state_manager.set_pending_action(
                conversation_id=conversation_id,
                action_type="find_indoor_activity",
                known_slots={"location": best_v["name"], "venues": [best_v["id"], alt_v["id"]]},
            )

        return {
            "answer": composed["answer"],
            "response": composed["response"],
            "intent": "recommend_indoor_activity",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "indoor_venues": venues,
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
        station_ids = GeospatialAgentService._extract_explicit_station_ids(query)
        return station_ids[0] if station_ids else None

    @staticmethod
    def _extract_explicit_station_ids(query: str) -> list[str]:
        """Return explicit station aliases in mention order, without duplicates."""
        station_ids: list[str] = []
        for match in re.finditer(r"\bS0?([1-5])\b", query, flags=re.IGNORECASE):
            station_id = f"S0{match.group(1)}"
            if station_id not in station_ids:
                station_ids.append(station_id)
        return station_ids

    @staticmethod
    def _extract_requested_station_comparison_count(query: str) -> int | None:
        match = re.search(r"\b([2-5])\s*(?:trạm|tram)\b", query, flags=re.IGNORECASE)
        return int(match.group(1)) if match else None

    @staticmethod
    def _station_target(
        station_id: str,
        station_data_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Build a map target from the canonical physical station registry."""
        station_data = station_data_map.get(station_id)
        registry_station = spatial_registry.get_station(station_id)
        if station_data is None or registry_station is None:
            raise ServiceError("station_not_found", "Requested station is not available", 404, {"station_id": station_id})

        score = environmental_scoring.score_candidate(station_data, activity="general")
        return {
            **station_data,
            **score,
            "id": f"station-{station_id}",
            "station_id": station_id,
            "sensor_id": station_id,
            "name": f"Trạm quan trắc {station_id}",
            "short_name": f"Trạm {station_id}",
            "category": "monitoring_station",
            "latitude": registry_station["latitude"],
            "longitude": registry_station["longitude"],
            "is_interpolated": False,
            "source_sensors": [station_id],
        }

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
