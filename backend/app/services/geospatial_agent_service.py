from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

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
            elif "san hô" in q:
                user_loc = (20.9935, 105.9405)
            elif "vinuni" in q:
                user_loc = (20.9898, 105.9467)
            elif "hải âu" in q or "ocean" in q:
                user_loc = (20.9945, 105.9585)
            elif "sao biển" in q:
                user_loc = (20.9985, 105.9525)

        # 6. Intent Determination & Dispatching

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

            # Safety Gate: If even the best route in the area exceeds safe thresholds, pivot to indoor venues!
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

                personalized_route = spatial_registry.generate_personalized_route(
                    user_lat=user_lat,
                    user_lng=user_lng,
                    target_km=target_distance_km,
                    base_circuit_id=best_base_circuit["id"],
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

        # Intent A: Compare Locations (e.g. "so sánh sapphire và hồ ngọc trai", "vinuni và hải âu")
        if any(w in q for w in ["so sánh", "so voi", "so với", "hơn không", "tốt hơn"]) or (
            " và " in q and any(w in q for w in ["chỗ nào", "đâu", "khu nào"])
        ):
            return self._handle_comparison_intent(q, ranked_pois, time_ctx, request_id)

        # Intent B: Worst Location / Most Polluted Area
        if any(w in q for w in ["ô nhiễm nhất", "kém nhất", "xấu nhất", "cao nhất", "nguy hiểm nhất", "tệ nhất"]):
            return self._handle_worst_location_intent(ranked_pois, time_ctx, request_id)

        # Intent C: Contextual Follow-up or Specific Location Focus
        # (e.g. User clicked a POI/Station and asked "tối nay thì sao?", "vinuni thế nào?", "hồ ngọc trai")
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

            # If user asks a specific question about a location
            if explicit_poi or is_forecast or any(w in q for w in ["thế nào", "sao", "chất lượng", "bao nhiêu", "có tốt"]):
                return self._handle_single_location_intent(target_poi, time_ctx, request_id)

        # Intent D: Best Location / Outdoor Activity Recommendation (Default rich flow)
        return self._handle_recommendation_intent(ranked_pois, activity, time_ctx, request_id, user_group)

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
    ) -> dict[str, Any]:
        best = ranked_pois[0]
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
    # INTENT HANDLER 2: Worst Location / Highest Pollution
    # -------------------------------------------------------------
    def _handle_worst_location_intent(
        self,
        ranked_pois: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        # Worst is candidate with lowest environmental score (highest AQI/PM2.5)
        worst = ranked_pois[-1]

        summary = (
            f"Khu vực **{worst['short_name']}** (gần trạm {worst['sensor_id']}) hiện có mức độ ô nhiễm không khí cao nhất "
            f"với AQI ghi nhận là **{worst['aqi']}** (PM2.5: {worst['pm25']} µg/m³)."
        )

        details = (
            f"• **Chỉ số đo lường:** AQI {worst['aqi']}, PM2.5: {worst['pm25']} µg/m³, CO₂: {worst['co2']} ppm, Độ ồn: {worst['noise_db']} dB.\n"
            f"• **Nguyên nhân tương quan:** Mật độ phương tiện giao thông qua lại cao kết hợp lưu thông gió chậm.\n"
            f"• **Khuyến nghị an toàn:** Cư dân nhạy cảm nên đeo khẩu trang lọc bụi mịn N95 và hạn chế lưu lại lâu tại điểm này."
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_sensor",
                "sensor_id": worst["sensor_id"],
                "severity": "danger",
                "lat": worst["latitude"],
                "lng": worst["longitude"],
            },
            {
                "type": "highlight_area",
                "area_id": worst["id"],
                "name": worst["short_name"],
                "lat": worst["latitude"],
                "lng": worst["longitude"],
                "radius_m": 300,
                "style": "danger",
            },
            {
                "type": "add_annotation",
                "target_id": worst["id"],
                "lat": worst["latitude"],
                "lng": worst["longitude"],
                "title": f"Cảnh báo: {worst['short_name']}",
                "subtitle": f"AQI {worst['aqi']} • PM2.5 {worst['pm25']} µg/m³ (Cao nhất khu vực)",
                "badge": "Ô nhiễm cao nhất",
                "style": "danger",
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
    # INTENT HANDLER 3: Compare Two or More Locations
    # -------------------------------------------------------------
    def _handle_comparison_intent(
        self,
        query: str,
        ranked_pois: list[dict[str, Any]],
        time_ctx: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        matched = []
        keywords = ["sapphire", "ngọc trai", "vinuni", "san hô", "hải âu", "vincom", "biển hồ", "nước mặn"]
        for p in ranked_pois:
            p_short = p["short_name"].lower()
            p_name = p["name"].lower()
            has_kw = any(kw in query and (kw in p_short or kw in p_name) for kw in keywords)
            if has_kw or p_short in query or p_name in query or p["sensor_id"].lower() in query:
                matched.append(p)

        if len(matched) < 2:
            matched = [ranked_pois[0], ranked_pois[-1]]

        cand_a = matched[0]
        cand_b = matched[1]

        winner = cand_a if cand_a["score"] >= cand_b["score"] else cand_b
        loser = cand_b if winner == cand_a else cand_a

        diff_aqi = abs(cand_a["aqi"] - cand_b["aqi"])
        diff_pm25 = round(abs(cand_a["pm25"] - cand_b["pm25"]), 1)

        summary = (
            f"So sánh giữa **{cand_a['short_name']}** và **{cand_b['short_name']}**: "
            f"Khu vực **{winner['short_name']}** có chất lượng môi trường tốt hơn rõ rệt (Điểm: {winner['score']} vs {loser['score']})."
        )

        details = (
            f"• **{winner['short_name']} (Thắng thế):** AQI {winner['aqi']}, PM2.5 {winner['pm25']} µg/m³, Độ ồn {winner['noise_db']} dB.\n"
            f"• **{loser['short_name']}:** AQI {loser['aqi']}, PM2.5 {loser['pm25']} µg/m³, Độ ồn {loser['noise_db']} dB.\n"
            f"• **Chênh lệch chính:** {winner['short_name']} có nồng độ bụi PM2.5 thấp hơn {diff_pm25} µg/m³ và chỉ số AQI tốt hơn {diff_aqi} điểm."
        )

        map_actions = [
            {"type": "clear_ai_layer"},
            {
                "type": "highlight_area",
                "area_id": winner["id"],
                "name": winner["short_name"],
                "lat": winner["latitude"],
                "lng": winner["longitude"],
                "radius_m": 220,
                "style": "recommended",
                "score": winner["score"],
            },
            {
                "type": "add_annotation",
                "target_id": winner["id"],
                "lat": winner["latitude"],
                "lng": winner["longitude"],
                "title": f"Tốt hơn: {winner['short_name']}",
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
        target_str = f"đáp ứng mục tiêu {target_req} km" if target_req else f"tổng cự ly {dist_km} km"

        summary = (
            f"{mode_prefix}Đã thiết lập **Lộ trình cá nhân hóa xuất phát từ vị trí của bạn** "
            f"({target_str}, Điểm phù hợp: {personalized_route['score']}/100, AQI {personalized_route['aqi']})."
        )

        details = (
            f"• **Lộ trình cá nhân hóa:** Xuất phát từ Vị trí của bạn → {personalized_route['circuit_entry_point']['name']} → {personalized_route['name']} ({dist_km} km, {personalized_route.get('laps', 1)} vòng).\n"
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
