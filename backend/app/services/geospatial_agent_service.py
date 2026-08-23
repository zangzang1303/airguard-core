from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from .conversational_agent_service import conversational_agent
from .environmental_scoring import environmental_scoring
from .live_telemetry_engine import live_engine
from .prophet_forecast_service import prophet_service
from .spatial_registry import spatial_registry
from .temporal_resolver import temporal_resolver


class GeospatialAgentService:
    """
    End-to-End Geospatial Interactive AI Agent Engine.
    Processes user questions with spatial map context, evaluates live & forecast
    environmental metrics without hardcoding, and synthesizes natural-language answers
    with declarative Leaflet map actions.
    """

    def process_query(
        self,
        message: str,
        user_id: str = "demo-user",
        station_id: str | None = None,
        map_context: dict[str, Any] | None = None,
        request_id: str = "geo-req-001",
        user_role: str = "resident",
        user_group: str = "normal",
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

        # 2. Extract User Location & Coordinates from Map Context
        user_loc = None
        if "user_location" in map_context and map_context["user_location"]:
            uloc = map_context["user_location"]
            if isinstance(uloc, dict) and "lat" in uloc and "lng" in uloc:
                user_loc = (float(uloc["lat"]), float(uloc["lng"]))
            elif isinstance(uloc, (list, tuple)) and len(uloc) >= 2:
                user_loc = (float(uloc[0]), float(uloc[1]))

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

        # 4. Fetch Base Data for Stations (Live or Forecast)
        station_data_map = {}
        history_map = live_engine.get_all_histories(hours=48)

        for s_id in ["S01", "S02", "S03", "S04", "S05"]:
            hist = history_map.get(s_id, [])
            if not is_forecast:
                # Realtime live snapshot
                current_st = live_engine.get_latest(s_id)
                station_data_map[s_id] = {
                    "station_id": s_id,
                    "pm25": current_st.get("pm25", 35.0),
                    "aqi": current_st.get("aqi", 95),
                    "co2": current_st.get("co2", 650.0),
                    "noise_db": current_st.get("noise_db", 55.0),
                    "temperature": current_st.get("temperature", 31.0),
                    "timestamp": current_st.get("measured_at", datetime.now(UTC).isoformat()),
                }
            else:
                # Prophet ML Multi-Step Forecast
                fc_res = prophet_service.forecast(s_id, hist, hours=max(1, forecast_hour), metric="pm25")
                horizons = fc_res.get("horizons", [])
                target_horizon = horizons[-1] if horizons else {}
                predicted_pm25 = target_horizon.get("predicted_value", 35.0)

                # Derived forecast metrics
                from .air_quality import pm25_aqi
                predicted_aqi = pm25_aqi(predicted_pm25)

                station_data_map[s_id] = {
                    "station_id": s_id,
                    "pm25": predicted_pm25,
                    "aqi": predicted_aqi,
                    "co2": 620.0,
                    "noise_db": 54.0 if forecast_hour >= 20 else 60.0,
                    "temperature": 29.5 if forecast_hour >= 18 else 32.5,
                    "timestamp": target_horizon.get("timestamp", datetime.now(UTC).isoformat()),
                    "lower_bound": target_horizon.get("lower_bound", predicted_pm25 * 0.85),
                    "upper_bound": target_horizon.get("upper_bound", predicted_pm25 * 1.15),
                }

        # 5. Populate All Candidate POIs with associated Station data
        candidate_pois = []
        for p in spatial_registry.list_pois():
            associated_st_id = p["sensor_id"]
            env = station_data_map.get(associated_st_id, station_data_map["S03"])
            cand = {
                **p,
                "pm25": env["pm25"],
                "aqi": env["aqi"],
                "co2": env["co2"],
                "noise_db": env["noise_db"],
                "temperature": env["temperature"],
                "timestamp": env["timestamp"],
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
            explicit_poi = spatial_registry.find_poi_by_name(q)
            target_poi = None
            if explicit_poi:
                target_poi = next((p for p in ranked_pois if p["id"] == explicit_poi["id"]), None)
            elif map_context.get("selected_location") or map_context.get("selected_sensor") or station_id:
                s_target = map_context.get("selected_sensor") or station_id
                target_poi = next((p for p in ranked_pois if p["sensor_id"] == s_target or p["id"] == map_context.get("selected_location")), ranked_pois[0])
            return self._handle_rain_or_precipitation_intent(q, target_poi, time_ctx, request_id)

        # Intent A: Compare Locations (e.g. "so sánh sapphire và hồ ngọc trai", "vinuni và hải âu")
        if any(w in q for w in ["so sánh", "so voi", "so với", "hơn không", "tốt hơn"]) or (
            " và " in q and any(w in q for w in ["chỗ nào", "đâu", "khu nào"])
        ):
            return self._handle_comparison_intent(q, ranked_pois, time_ctx, request_id)

        # Intent B: Worst Location / Most Polluted Area
        if any(w in q for w in ["ô nhiễm nhất", "kém nhất", "xấu nhất", "cao nhất", "nguy hiểm nhất", "tệ nhất"]):
            return self._handle_worst_location_intent(ranked_pois, time_ctx, request_id)

        # Intent 0: Running Route Recommendation (Personalized or General)
        is_route_query = (
            any(w in q for w in ["đoạn đường", "cung đường", "tuyến đường", "lộ trình", "đường chạy", "chạy bộ ở đâu", "tuyến chạy", "chạy ở đâu", "tuyến nào", "đường nào", "chạy bộ"])
            or target_distance_km is not None
            or (activity == "running" and any(w in q for w in ["đường", "tuyến", "đoạn", "ở đâu", "lộ trình", "nơi nào", "chỗ nào"]))
        )
        if is_route_query:
            candidate_routes = []
            for r in spatial_registry.list_routes():
                associated_st_id = r["sensor_id"]
                env = station_data_map.get(associated_st_id, station_data_map["S03"])
                cand_r = {
                    **r,
                    "pm25": env["pm25"],
                    "aqi": env["aqi"],
                    "co2": env["co2"],
                    "noise_db": env["noise_db"],
                    "temperature": env["temperature"],
                    "timestamp": env["timestamp"],
                }
                candidate_routes.append(cand_r)

            ranked_routes = environmental_scoring.rank_routes(
                candidate_routes, user_group=user_group, user_location=user_loc
            )

            # The route catalog supplies environmental coverage, but requested
            # distances are planned dynamically below rather than matched to a
            # pre-written circuit.
            best_base_circuit = ranked_routes[0]
            safety_eval = environmental_scoring.check_outdoor_exercise_safety(
                {
                    "aqi": best_base_circuit["aqi"],
                    "pm25": best_base_circuit["pm25"],
                    "temperature": best_base_circuit["temperature"],
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

            # If user specified a starting location or target distance, generate dynamic personalized route!
            if user_loc or target_distance_km:
                user_lat = user_loc[0] if user_loc else best_base_circuit["start_point"]["lat"]
                user_lng = user_loc[1] if user_loc else best_base_circuit["start_point"]["lng"]
                station_pm25_map = {
                    station: float(values["pm25"])
                    for station, values in station_data_map.items()
                }

                personalized_route = spatial_registry.generate_personalized_route(
                    user_lat=user_lat,
                    user_lng=user_lng,
                    target_km=target_distance_km,
                    base_circuit_id=best_base_circuit["id"],
                    station_pm25_map=station_pm25_map,
                )

                personalized_route.update(
                    {
                        "pm25": best_base_circuit["pm25"],
                        "aqi": best_base_circuit["aqi"],
                        "co2": best_base_circuit["co2"],
                        "noise_db": best_base_circuit["noise_db"],
                        "temperature": best_base_circuit["temperature"],
                        "timestamp": best_base_circuit["timestamp"],
                        "score": best_base_circuit["score"],
                        "tier": best_base_circuit["tier"],
                    }
                )

                return self._handle_personalized_route_intent(
                    personalized_route=personalized_route,
                    best_base_circuit=best_base_circuit,
                    time_ctx=time_ctx,
                    request_id=request_id,
                )

            return self._handle_running_route_intent(ranked_routes, time_ctx, request_id)

        # Intent C: Specific Metric Focus (Noise, Temp, PM2.5/CO2) or Single Location / Follow-up Inquiry
        is_noise_inquiry = any(w in q for w in ["độ ồn", "tiếng ồn", "ồn không", "yên tĩnh", "ồn ào", "ồn thế nào"])
        is_temp_inquiry = any(w in q for w in ["nhiệt độ", "nóng không", "mát không", "nhiệt độ bao nhiêu", "bao nhiêu độ"])

        explicit_poi = spatial_registry.find_poi_by_name(q)
        if explicit_poi or map_context.get("selected_location") or map_context.get("selected_sensor") or station_id:
            if explicit_poi:
                target_poi = next((p for p in ranked_pois if p["id"] == explicit_poi["id"]), ranked_pois[0])
            elif map_context.get("selected_location"):
                target_poi = next(
                    (p for p in ranked_pois if p["id"] == map_context["selected_location"] or p["short_name"].lower() in str(map_context["selected_location"]).lower()),
                    ranked_pois[0],
                )
            elif map_context.get("selected_sensor") or station_id:
                s_target = map_context.get("selected_sensor") or station_id
                target_poi = next((p for p in ranked_pois if p["sensor_id"] == s_target), ranked_pois[0])
            else:
                target_poi = ranked_pois[0]

            if is_noise_inquiry:
                return self._handle_specific_noise_intent(target_poi, time_ctx, request_id)
            if is_temp_inquiry:
                return self._handle_specific_temp_intent(target_poi, time_ctx, request_id)

            # If user asks a specific question about a location or follow-up
            if (
                explicit_poi
                or is_forecast
                or map_context.get("selected_location")
                or map_context.get("selected_sensor")
                or any(w in q for w in ["thế nào", "sao", "chất lượng", "bao nhiêu", "có tốt", "chỗ này", "ở đây", "khu này", "nơi này", "vị trí này", "thì sao", "như nào"])
            ):
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
    def _handle_rain_or_precipitation_intent(
        self,
        q: str,
        poi: dict[str, Any] | None,
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
        location_name = poi["short_name"] if poi else "Vinhomes Ocean Park 1"

        summary = (
            f"Hệ thống AirGuard AI hiện tại **chưa trang bị cảm biến đo lượng mưa hoặc radar dự báo mưa thời gian thực** "
            f"(nằm ngoài phạm vi quan trắc của mạng lưới cảm biến không khí & môi trường)."
        )

        if poi:
            details = (
                f"• **Thông số vi khí hậu ghi nhận tại {location_name}:** "
                f"Nhiệt độ hiện tại: **{poi['temperature']}°C**, Độ ồn: **{poi['noise_db']} dB**, "
                f"Chất lượng không khí AQI: **{poi['aqi']}** (PM2.5: {poi['pm25']} µg/m³ - Đánh giá: {poi['tier'].upper()}).\n"
                f"• **Phạm vi hệ thống:** AirGuard tập trung giám sát các chỉ số chất lượng không khí (AQI, PM2.5, CO₂), nhiệt độ, độ ồn và cảnh báo ô nhiễm.\n"
                f"• **Khuyến nghị:** Để biết chính xác tại {location_name} có mưa hay không hoặc theo dõi ảnh mây vệ tinh, bạn vui lòng tra cứu thêm tại ứng dụng thời tiết chuyên dụng (như AccuWeather hoặc Trung tâm Khí tượng Thủy văn)."
            )
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
            details = (
                "• **Phạm vi hệ thống:** Mạng lưới cảm biến AirGuard tại Ocean Park 1 chuyên quan trắc "
                "chất lượng không khí (AQI, PM2.5, CO₂), nhiệt độ và độ ồn môi trường.\n"
                "• **Khuyến nghị:** Để theo dõi mây radar và khả năng mưa chính xác, vui lòng tham khảo ứng dụng thời tiết chuyên dụng."
            )
            map_actions = [{"type": "clear_ai_layer"}]

        return {
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "unsupported_precipitation_weather",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [
                {"source": "system_capability", "scope": "air_quality_and_microclimate", "status": "unsupported_rain_sensor"}
            ] + ([{"source": "sensor", "poi_id": poi["id"], "metric": "temperature", "value": poi["temperature"], "timestamp": poi["timestamp"]}] if poi else []),
            "map_actions": map_actions,
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
        summary = "Yêu cầu này nằm ngoài phạm vi hoạt động của hệ thống AirGuard AI."
        details = (
            "AirGuard AI là trợ lý thông minh chuyên về **giám sát chất lượng không khí (AQI, PM2.5, CO₂), cảnh báo ô nhiễm và gợi ý lộ trình vận động ngoài trời an toàn** tại Vinhomes Ocean Park 1.\n\n"
            "👉 **Bạn có thể hỏi mình về:**\n"
            "• Chất lượng không khí hiện tại hoặc dự báo 1-3h tới tại các phân khu (San Hô, Hồ Ngọc Trai, VinUni, Sapphire, Sao Biển...).\n"
            "• So sánh độ trong lành giữa các địa điểm để chọn nơi vui chơi, đi dạo.\n"
            "• Gợi ý cung đường chạy bộ / đạp xe tối nay với cự ly mong muốn."
        )
        return {
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "out_of_scope",
            "evidence": [],
            "map_actions": [{"type": "clear_ai_layer"}],
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
        summary = f"Độ ồn hiện tại tại **{poi['short_name']}** là **{noise} dB** ({level_str})."
        details = (
            f"• **Đánh giá âm học:** Mức {noise} dB đạt chuẩn QCVN 26:2010/BTNMT, "
            f"{'rất thích hợp cho các hoạt động thư giãn, đọc sách hoặc đi dạo' if noise <= 60 else 'phù hợp sinh hoạt thông thường'}.\n"
            f"• **Các chỉ số kèm theo:** Nhiệt độ: {poi['temperature']}°C, AQI: {poi['aqi']} (PM2.5: {poi['pm25']} µg/m³)."
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
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "get_noise_metric",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [{"source": "sensor", "poi_id": poi["id"], "metric": "noise_db", "value": noise, "timestamp": poi["timestamp"]}],
            "map_actions": map_actions,
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
        temp_str = "mát mẻ, dễ chịu" if temp < 28 else ("khá ấm áp" if temp <= 33 else "nắng nóng")
        summary = f"Nhiệt độ hiện tại tại **{poi['short_name']}** là **{temp}°C** ({temp_str})."
        details = (
            f"• **Vi khí hậu:** Nhiệt độ {temp}°C kết hợp không gian thoáng rộng quanh khu vực {poi['short_name']}.\n"
            f"• **Chất lượng không khí:** AQI đạt {poi['aqi']} (PM2.5: {poi['pm25']} µg/m³), Độ ồn: {poi['noise_db']} dB."
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
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "get_temperature_metric",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [{"source": "sensor", "poi_id": poi["id"], "metric": "temperature", "value": temp, "timestamp": poi["timestamp"]}],
            "map_actions": map_actions,
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

        activity_label = {
            "running": "chạy bộ",
            "walking": "đi dạo tản bộ",
            "children_play": "vui chơi ngoài trời cho trẻ nhỏ",
            "elderly_stroll": "dạo bộ cho người cao tuổi",
            "dining_outdoor": "ngồi ngoài trời & cafe",
            "general": "hoạt động ngoài trời",
        }.get(activity, "hoạt động ngoài trời")

        time_label = time_ctx["label"]
        mode_prefix = f"[{time_label.upper()}] " if time_ctx["is_forecast"] else ""

        summary = (
            f"{mode_prefix}Khu vực **{best['short_name']}** là địa điểm phù hợp nhất để {activity_label} "
            f"(Điểm chất lượng: {best['score']}/100, AQI {best['aqi']})."
        )

        details = (
            f"• **Lựa chọn #1 ({best['short_name']}):** AQI {best['aqi']}, PM2.5: {best['pm25']} µg/m³, "
            f"Nhiệt độ: {best['temperature']}°C, Độ ồn: {best['noise_db']} dB. Không gian thoáng rộng, nồng độ bụi mịn ở ngưỡng an toàn.\n"
            f"• **Lựa chọn #2 ({alt['short_name']}):** AQI {alt['aqi']} (Điểm: {alt['score']}/100), thích hợp làm phương án thay thế.\n"
            f"• **Lưu ý hạn chế:** Khu vực {worst['short_name']} đang có AQI {worst['aqi']} (PM2.5: {worst['pm25']} µg/m³), khuyến nghị tránh tập luyện nặng tại đây."
        )

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
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "recommend_outdoor_location",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": evidence,
            "map_actions": map_actions,
            "request_id": request_id,
        }

    # -------------------------------------------------------------
    # INTENT HANDLER 2: Find Worst / Most Polluted Location
    # -------------------------------------------------------------
    def _handle_worst_location_intent(
        self,
        ranked_pois: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        # Worst is the last item in ascending ranked list (lowest score, highest pollution)
        worst = ranked_pois[-1]
        time_label = time_ctx["label"]
        mode_prefix = f"[{time_label.upper()}] " if time_ctx["is_forecast"] else ""

        summary = (
            f"{mode_prefix}Khu vực **{worst['short_name']}** (Trạm {worst['sensor_id']}) "
            f"hiện đang có chất lượng không khí kém nhất với AQI **{worst['aqi']}** (PM2.5: {worst['pm25']} µg/m³)."
        )

        details = (
            f"• **Thông số ô nhiễm:** Nồng độ PM2.5 là {worst['pm25']} µg/m³, Độ ồn: {worst['noise_db']} dB, "
            f"Nhiệt độ: {worst['temperature']}°C.\n"
            f"• **Khuyến cáo:** Tránh tập thể dục cường độ cao ngoài trời tại khu vực này. Người có bệnh lý hô hấp hoặc tim mạch nên hạn chế tiếp xúc lâu."
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_sensor",
                "sensor_id": worst["sensor_id"],
                "lat": worst["latitude"],
                "lng": worst["longitude"],
                "severity": "danger" if worst["aqi"] > 100 else "warning",
                "aqi": worst["aqi"],
            },
            {
                "type": "add_annotation",
                "target_id": worst["sensor_id"],
                "lat": worst["latitude"],
                "lng": worst["longitude"],
                "title": f"⚠️ Điểm ô nhiễm: {worst['short_name']}",
                "subtitle": f"{time_label} • AQI {worst['aqi']} (PM2.5: {worst['pm25']} µg/m³)",
                "badge": "Khu vực ô nhiễm nhất",
                "style": "avoid",
            },
            {
                "type": "fly_to",
                "lat": worst["latitude"],
                "lng": worst["longitude"],
                "zoom": 16,
            },
        ]

        return {
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "find_worst_location",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [
                {"source": "sensor", "station_id": worst["sensor_id"], "metric": "aqi", "value": worst["aqi"], "timestamp": worst["timestamp"]},
                {"source": "sensor", "station_id": worst["sensor_id"], "metric": "pm25", "value": worst["pm25"], "timestamp": worst["timestamp"]},
            ],
            "map_actions": map_actions,
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
    ) -> dict[str, Any]:
        time_label = time_ctx["label"]
        q_low = query.lower()

        found = []
        alias_map = [
            ("sapphire", "poi_sapphire"),
            ("ngọc trai", "poi_ngoc_trai_lake"),
            ("hồ ngọc trai", "poi_ngoc_trai_lake"),
            ("vinuni", "poi_vinuni"),
            ("san hô", "poi_san_ho_park"),
            ("san ho", "poi_san_ho_park"),
            ("hải âu", "poi_hai_au"),
            ("hai au", "poi_hai_au"),
            ("biển hồ", "poi_salt_lake"),
            ("vincom", "poi_vincom"),
        ]
        for alias, p_id in alias_map:
            if alias in q_low:
                poi_match = next((p for p in ranked_pois if p["id"] == p_id), None)
                if poi_match and poi_match not in found:
                    found.append(poi_match)

        if len(found) >= 2:
            cand_a, cand_b = found[0], found[1]
        elif len(found) == 1:
            cand_a = found[0]
            cand_b = next((p for p in ranked_pois if p["id"] != cand_a["id"]), ranked_pois[-1])
        else:
            cand_a = ranked_pois[0]
            cand_b = ranked_pois[1] if len(ranked_pois) > 1 else ranked_pois[0]

        winner = cand_a if cand_a["score"] >= cand_b["score"] else cand_b
        loser = cand_b if winner["id"] == cand_a["id"] else cand_a

        summary = (
            f"So sánh giữa **{winner['short_name']}** và **{loser['short_name']}**: "
            f"Khu vực **{winner['short_name']}** có môi trường tốt hơn với AQI **{winner['aqi']}** "
            f"(Điểm đánh giá: {winner['score']}/100 so với {loser['score']}/100 của {loser['short_name']})."
        )

        details = (
            f"• **{winner['short_name']} (Tốt hơn):** AQI {winner['aqi']}, PM2.5: {winner['pm25']} µg/m³, "
            f"Nhiệt độ: {winner['temperature']}°C, Độ ồn: {winner['noise_db']} dB.\n"
            f"• **{loser['short_name']}:** AQI {loser['aqi']}, PM2.5: {loser['pm25']} µg/m³, "
            f"Nhiệt độ: {loser['temperature']}°C, Độ ồn: {loser['noise_db']} dB.\n"
            f"• **Kết luận:** {winner['short_name']} có nồng độ bụi mịn thấp hơn {abs(round(winner['pm25'] - loser['pm25'], 1))} µg/m³, không gian thoáng đãng hơn."
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_area",
                "area_id": winner["id"],
                "name": winner["short_name"],
                "lat": winner["latitude"],
                "lng": winner["longitude"],
                "radius_m": 250,
                "style": "recommended",
                "score": winner["score"],
            },
            {
                "type": "add_annotation",
                "target_id": winner["id"],
                "lat": winner["latitude"],
                "lng": winner["longitude"],
                "title": f"🏆 Tốt hơn: {winner['short_name']}",
                "subtitle": f"AQI {winner['aqi']} • PM2.5 {winner['pm25']} µg/m³ (Điểm {winner['score']})",
                "badge": "Vượt trội hơn",
                "style": "recommended",
            },
            {
                "type": "highlight_area",
                "area_id": loser["id"],
                "name": loser["short_name"],
                "lat": loser["latitude"],
                "lng": loser["longitude"],
                "radius_m": 220,
                "style": "caution",
                "score": loser["score"],
            },
            {
                "type": "add_annotation",
                "target_id": loser["id"],
                "lat": loser["latitude"],
                "lng": loser["longitude"],
                "title": f"{loser['short_name']}",
                "subtitle": f"AQI {loser['aqi']} • PM2.5 {loser['pm25']} µg/m³",
                "badge": "Chất lượng kém hơn",
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
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "compare_locations",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [
                {"source": "sensor", "poi_id": cand_a["id"], "metric": "aqi", "value": cand_a["aqi"], "timestamp": cand_a["timestamp"]},
                {"source": "sensor", "poi_id": cand_b["id"], "metric": "aqi", "value": cand_b["aqi"], "timestamp": cand_b["timestamp"]},
            ],
            "map_actions": map_actions,
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
        mode_str = f"Dự báo ({time_label})" if time_ctx["is_forecast"] else "Hiện tại"

        summary = (
            f"{mode_str} tại **{poi['short_name']}**: Chỉ số AQI đạt **{poi['aqi']}**, "
            f"PM2.5: {poi['pm25']} µg/m³ (Đánh giá mức độ phù hợp: {poi['score']}/100)."
        )

        details = (
            f"• **Thông số chi tiết:** PM2.5: {poi['pm25']} µg/m³, CO₂: {poi['co2']} ppm, "
            f"Nhiệt độ: {poi['temperature']}°C, Độ ồn: {poi['noise_db']} dB.\n"
            f"• **Khuyến nghị sinh hoạt:** {'Không khí trong lành, rất thích hợp cho các hoạt động ngoài trời.' if poi['aqi'] <= 100 else 'Chất lượng không khí ở mức trung bình - kém, người nhạy cảm nên chú ý.'}"
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_point",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "name": poi["short_name"],
                "style": poi["tier"],
            },
            {
                "type": "add_annotation",
                "target_id": poi["id"],
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "title": poi["short_name"],
                "subtitle": f"{time_label} • AQI {poi['aqi']} (PM2.5 {poi['pm25']} µg/m³)",
                "badge": f"Điểm: {poi['score']}/100",
                "style": poi["tier"],
            },
            {
                "type": "fly_to",
                "lat": poi["latitude"],
                "lng": poi["longitude"],
                "zoom": 16,
            },
        ]

        return {
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "get_location_environment",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": [
                {"source": "forecast" if time_ctx["is_forecast"] else "sensor", "poi_id": poi["id"], "metric": "aqi", "value": poi["aqi"], "timestamp": poi["timestamp"]},
                {"source": "forecast" if time_ctx["is_forecast"] else "sensor", "poi_id": poi["id"], "metric": "pm25", "value": poi["pm25"], "timestamp": poi["timestamp"]},
            ],
            "map_actions": map_actions,
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
    ) -> dict[str, Any]:
        best = ranked_routes[0]
        alt = ranked_routes[1] if len(ranked_routes) > 1 else best

        time_label = time_ctx["label"]
        mode_prefix = f"[{time_label.upper()}] " if time_ctx["is_forecast"] else ""

        summary = (
            f"{mode_prefix}Cung đường **{best['name']}** (Cự ly: {best['distance_km']} km) "
            f"là lộ trình chạy bộ phù hợp nhất với chất lượng không khí trong lành (Điểm: {best['score']}/100, AQI {best['aqi']})."
        )

        details = (
            f"• **Lộ trình #1 ({best['short_name']}):** Cự ly {best['distance_km']} km. "
            f"AQI {best['aqi']} (PM2.5: {best['pm25']} µg/m³), Nhiệt độ: {best['temperature']}°C, Độ ồn: {best['noise_db']} dB.\n"
            f"• **Điểm xuất phát gợi ý:** {best['start_point']['name']}.\n"
            f"• **Đặc điểm đường chạy:** {best['surface']}. {best['traffic_conflict']}.\n"
            f"• **Điểm nổi bật:** {best['highlights']}.\n"
            f"• **Lựa chọn dự phòng:** Tuyến {alt['name']} ({alt['distance_km']} km, Điểm: {alt['score']}/100, AQI {alt['aqi']})."
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
                "distance_km": best["distance_km"],
                "style": "recommended",
                "score": best["score"],
                "rank": 1,
            },
            {
                "type": "add_annotation",
                "target_id": f"{best['id']}_start",
                "lat": best["start_point"]["lat"],
                "lng": best["start_point"]["lng"],
                "title": f"🚩 Xuất phát: {best['short_name']}",
                "subtitle": f"{time_label} • Cự ly {best['distance_km']} km • AQI {best['aqi']} (Điểm: {best['score']})",
                "badge": "Lộ trình tối ưu #1",
                "style": "recommended",
            },
        ]

        if alt and alt["id"] != best["id"]:
            map_actions.append(
                {
                    "type": "highlight_route",
                    "route_id": alt["id"],
                    "name": alt["name"],
                    "short_name": alt["short_name"],
                    "coordinates": alt["coordinates"],
                    "distance_km": alt["distance_km"],
                    "style": "alternative",
                    "score": alt["score"],
                    "rank": 2,
                }
            )

        map_actions.append(
            {
                "type": "fit_bounds",
                "bounds": bounds,
                "padding": [60, 60],
            }
        )

        evidence = [
            {
                "source": "forecast" if time_ctx["is_forecast"] else "sensor",
                "route_id": best["id"],
                "station_id": best["sensor_id"],
                "metric": "aqi",
                "value": best["aqi"],
                "timestamp": best["timestamp"],
            },
            {
                "source": "forecast" if time_ctx["is_forecast"] else "sensor",
                "route_id": best["id"],
                "station_id": best["sensor_id"],
                "metric": "pm25",
                "value": best["pm25"],
                "timestamp": best["timestamp"],
            },
            {
                "source": "route_scoring",
                "route_id": best["id"],
                "distance_km": best["distance_km"],
                "score": best["score"],
            },
        ]

        return {
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "recommend_running_route",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "evidence": evidence,
            "map_actions": map_actions,
            "request_id": request_id,
        }

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

        summary = (
            f"⚠️ **CẢNH BÁO MÔI TRƯỜNG ({time_label.upper()}):** {safety_eval['warning']}\n"
            f"💡 **Khuyến nghị y tế:** Không nên chạy bộ ngoài trời. Bạn nên chuyển sang vận động trong nhà tại **{best_v['name']}** để bảo vệ đường hô hấp."
        )

        details = (
            f"• **Địa điểm trong nhà ưu tiên #1:** {best_v['name']} (Giờ mở cửa: {best_v['operating_hours']}).\n"
            f"  - Hoạt động gợi ý: {', '.join(best_v['activities'])}.\n"
            f"  - Tiện ích: {best_v['description']}\n"
            f"• **Địa điểm lựa chọn #2:** {alt_v['name']} ({', '.join(alt_v['activities'][:2])}).\n"
            f"• **Lời khuyên an toàn:** Khi nồng độ bụi mịn PM2.5 vượt ngưỡng, lưu lượng thông khí phổi khi chạy bộ ngoài trời tăng gấp 5–10 lần, hít trực tiếp bụi mịn sâu vào phế nang."
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
                "title": f"🏊 {best_v['short_name']}",
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
                "title": f"🏋️ {alt_v['short_name']}",
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
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "recommend_indoor_activity",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "safety_status": safety_eval,
            "indoor_venues": venues,
            "evidence": [
                {
                    "source": "safety_engine",
                    "reason": safety_eval["reason"],
                    "aqi": safety_eval.get("aqi"),
                    "pm25": safety_eval.get("pm25"),
                },
                {"source": "indoor_catalog", "venue_id": best_v["id"], "name": best_v["name"]},
            ],
            "map_actions": map_actions,
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
        mode_prefix = f"[{time_label.upper()}] " if time_ctx["is_forecast"] else ""

        dist_km = personalized_route["distance_km"]
        target_req = personalized_route.get("target_requested_km")
        if target_req:
            target_str = f"mục tiêu {target_req} km, cự ly ước tính {dist_km} km"
        else:
            target_str = f"tổng cự ly {dist_km} km"

        summary = (
            f"{mode_prefix}Đã thiết lập **Lộ trình cá nhân hóa xuất phát từ vị trí của bạn** "
            f"({target_str}, Điểm phù hợp: {personalized_route['score']}/100, AQI {personalized_route['aqi']})."
        )

        details = (
            f"• **Lộ trình cá nhân hóa:** Xuất phát từ Vị trí của bạn → {personalized_route['circuit_entry_point']['name']} → {personalized_route['name']} ({dist_km} km).\n"
            f"• **Chất lượng môi trường:** AQI {personalized_route['aqi']} (PM2.5: {personalized_route['pm25']} µg/m³), Nhiệt độ: {personalized_route['temperature']}°C, Độ ồn: {personalized_route['noise_db']} dB.\n"
            f"• **Đặc điểm đường chạy:** {personalized_route['surface']}. {personalized_route['traffic_conflict']}.\n"
            f"• **Điểm nổi bật:** {personalized_route['highlights']}"
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
            "answer": {"summary": summary, "details": details},
            "response": f"{summary}\n\n{details}",
            "intent": "recommend_personalized_running_route",
            "time_context": time_ctx,
            "data_mode": time_ctx["type"],
            "personalized_route": personalized_route,
            "evidence": evidence,
            "map_actions": map_actions,
            "request_id": request_id,
        }


geospatial_agent = GeospatialAgentService()
