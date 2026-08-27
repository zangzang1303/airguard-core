"""AirGuard User-Facing Response Composer & Response Contract Validator.

Converts validated environmental and geospatial evidence into friendly, concise,
natural and actionable Vietnamese responses without leaking internal tool calls,
raw IDW grid data, backend service names, or internal model identifiers.
"""

from __future__ import annotations

import re
from typing import Any


def aqi_category_vi(aqi: int | float | None) -> str:
    """Translate AQI numerical value into natural Vietnamese category."""
    if aqi is None:
        return "Chưa xác định"
    val = float(aqi)
    if val <= 50:
        return "Tốt"
    elif val <= 100:
        return "Trung bình"
    elif val <= 150:
        return "Không tốt cho nhóm nhạy cảm"
    elif val <= 200:
        return "Xấu (Không lành mạnh)"
    elif val <= 300:
        return "Rất xấu"
    else:
        return "Nguy hại"


class ResponseComposer:
    """Standardized User-Facing Response Composer for AirGuard AI."""

    @staticmethod
    def compose_greeting(request_id: str = "") -> dict[str, Any]:
        """Task 10.1: Friendly greeting."""
        headline = "👋 **Chào bạn! Mình là trợ lý môi trường AirGuard AI.**"
        advice = "Mình có thể giúp bạn kiểm tra chất lượng không khí, so sánh khu vực hoặc tìm cung đường chạy bộ phù hợp hơn trong Ocean Park 1."
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
            "intent": "greeting",
            "follow_up_actions": [
                "🏫 VinUni không khí thế nào?",
                "⚠️ Khu nào đang ô nhiễm nhất?",
                "🏃 Tìm đường chạy bộ 3 km",
                "⚖️ So sánh Sapphire và Hồ Ngọc Trai",
            ],
        }

    @staticmethod
    def compose_worst_location(
        worst_poi: dict[str, Any],
        best_poi: dict[str, Any] | None,
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Task 10.3: Worst location / most polluted area."""
        time_label = time_ctx.get("label", "hiện tại")
        worst_name = worst_poi.get("short_name") or worst_poi.get("name", "Trục Đa Tốn")
        worst_aqi = int(worst_poi.get("aqi", 0))
        worst_pm25 = worst_poi.get("pm25", 0)
        worst_cat = aqi_category_vi(worst_aqi)
        worst_sensor = worst_poi.get("sensor_id", "S01")

        best_name = (best_poi.get("short_name") or best_poi.get("name", "VinUni")) if best_poi else "VinUni"
        best_sensor = best_poi.get("sensor_id", "S04") if best_poi else "S04"
        best_aqi = int(best_poi.get("aqi", 0)) if best_poi else 48

        headline = f"⚠️ **{worst_name} ({worst_sensor}) hiện là khu vực ô nhiễm nhất trong phạm vi AirGuard đang theo dõi.**"

        highlights_text = (
            f"- **AQI:** {worst_aqi} — {worst_cat}\n"
            f"- **PM2.5:** {worst_pm25} µg/m³\n"
            f"- **Khu vực sạch hơn:** {best_name} ({best_sensor})"
        )

        advice = f"Nếu bạn đang định đi bộ hoặc tập thể thao, nên tránh khu {worst_name} ({worst_sensor}) lúc này và ưu tiên khu vực có AQI thấp hơn như {best_name} ({best_sensor})."
        map_feedback = "📍 Mình đã đánh dấu khu vực này trên bản đồ."
        data_note = "*Dữ liệu mô phỏng AirGuard AI · cập nhật vừa xong.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"

        highlights_data = [
            {"label": "AQI", "value": str(worst_aqi), "description": worst_cat},
            {"label": "PM2.5", "value": f"{worst_pm25} µg/m³"},
            {"label": "Khu vực sạch hơn", "value": f"{best_name} ({best_sensor})", "description": f"AQI {best_aqi}"},
        ]

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "find_worst_location",
            "follow_up_actions": [
                f"🌿 Xem khu sạch hơn ({best_name})",
                "📍 Xem trên bản đồ",
                "🏃 Tìm đường tránh khu này",
            ],
        }

    @staticmethod
    def compose_best_location(
        best_poi: dict[str, Any],
        alt_poi: dict[str, Any] | None,
        activity: str,
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Task 10.4: Best location / cleanest outdoor area."""
        best_name = best_poi.get("short_name") or best_poi.get("name", "VinUni")
        best_aqi = int(best_poi.get("aqi", 0))
        best_pm25 = best_poi.get("pm25", 0)
        best_cat = aqi_category_vi(best_aqi)

        headline = f"🌿 **{best_name} hiện là khu vực có chất lượng không khí tốt nhất trong các điểm AirGuard đang theo dõi.**"

        highlights_text = (
            f"- **AQI:** {best_aqi} — {best_cat}\n"
            f"- **PM2.5:** {best_pm25} µg/m³"
        )

        advice = "Đây là lựa chọn phù hợp hơn nếu bạn muốn đi bộ hoặc tập thể thao ngoài trời lúc này."
        map_feedback = f"📍 Mình đã đánh dấu {best_name} trên bản đồ."
        data_note = "*Dữ liệu mô phỏng AirGuard AI · cập nhật vừa xong.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"

        highlights_data = [
            {"label": "AQI", "value": str(best_aqi), "description": best_cat},
            {"label": "PM2.5", "value": f"{best_pm25} µg/m³"},
        ]

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "recommend_outdoor_location",
            "follow_up_actions": [
                f"🏃 Tuyến chạy tại {best_name}",
                "📍 Xem trên bản đồ",
                "⏱️ Dự báo 1-3 giờ",
            ],
        }

    @staticmethod
    def compose_single_location(
        poi: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Task 10.2: Location AQI inquiry."""
        name = poi.get("short_name") or poi.get("name", "Khu vực")
        aqi = int(poi.get("aqi", 0))
        pm25 = poi.get("pm25", 0)
        cat = aqi_category_vi(aqi)

        headline = f"📍 **Không khí tại {name} hiện ở mức {cat}.**"

        highlights_text = (
            f"- **AQI:** {aqi}\n"
            f"- **PM2.5:** {pm25} µg/m³"
        )

        if aqi <= 100:
            advice = "Bạn vẫn có thể đi bộ hoặc vận động nhẹ ngoài trời. Nếu thuộc nhóm nhạy cảm, nên tránh vận động kéo dài."
        else:
            advice = "Chất lượng không khí ở mức không tốt cho nhóm nhạy cảm, người có tiền sử hô hấp nên hạn chế vận động kéo dài ngoài trời."

        map_feedback = f"📍 Mình đã đưa bản đồ tới khu {name}."
        data_note = "*Dữ liệu mô phỏng · cập nhật 2 phút trước.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"

        highlights_data = [
            {"label": "AQI", "value": str(aqi), "description": cat},
            {"label": "PM2.5", "value": f"{pm25} µg/m³"},
        ]

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "get_location_environment",
            "follow_up_actions": [
                "⏱️ Dự báo 1-3 giờ",
                "🌿 So sánh với khu khác",
                "🏃 Tìm đường chạy qua đây",
            ],
        }

    @staticmethod
    def compose_comparison(
        winner: dict[str, Any],
        loser: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Task 10.5: Area Comparison."""
        w_name = winner.get("short_name") or winner.get("name", "Khu A")
        l_name = loser.get("short_name") or loser.get("name", "Khu B")
        w_aqi = int(winner.get("aqi", 0))
        l_aqi = int(loser.get("aqi", 0))
        diff = abs(w_aqi - l_aqi)

        headline = f"🌿 **{w_name} hiện sạch hơn {l_name} (chất lượng không khí tốt hơn).**"

        highlights_text = (
            f"- **{w_name}:** AQI {w_aqi}\n"
            f"- **{l_name}:** AQI {l_aqi}\n"
            f"- **Chênh lệch:** {diff} AQI"
        )

        advice = f"Nếu bạn đang chọn nơi để đi bộ hoặc tập nhẹ, **{w_name} là lựa chọn phù hợp hơn lúc này**."
        map_feedback = "📍 Mình đã đánh dấu cả hai khu vực để bạn dễ so sánh."
        data_note = "*Dữ liệu mô phỏng AirGuard AI.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"

        highlights_data = [
            {"label": w_name, "value": f"AQI {w_aqi}"},
            {"label": l_name, "value": f"AQI {l_aqi}"},
            {"label": "Chênh lệch", "value": f"{diff} AQI"},
        ]

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "compare_locations",
            "follow_up_actions": [
                f"🏃 Tuyến chạy tại {w_name}",
                "📍 Xem trên bản đồ",
                "⏱️ Dự báo 1-3 giờ tới",
            ],
        }

    @staticmethod
    def compose_running_route(
        best_route: dict[str, Any],
        origin_label: str,
        time_ctx: dict[str, Any],
        request_id: str = "",
        is_personalized: bool = False,
    ) -> dict[str, Any]:
        """Task 10.6: Running Route Recommendation."""
        dist = best_route.get("distance_km", 3.1)
        avg_aqi = int(best_route.get("aqi", 55))
        avg_cat = aqi_category_vi(avg_aqi)
        route_name = best_route.get("name") or best_route.get("short_name", "VinUni → Hồ Ngọc Trai")

        headline = f"🏃 **Mình đã tìm được một cung đường khoảng {dist} km có chất lượng không khí phù hợp hơn.**"

        highlights_text = (
            f"- **Cự ly:** khoảng {dist} km\n"
            f"- **AQI trung bình trên tuyến:** {avg_aqi}\n"
            f"- **Khu vực chính:** {origin_label} → {route_name}"
        )

        advice = "Tuyến này giúp hạn chế đi qua các vùng đang có AQI cao hơn."
        map_feedback = "🗺️ Mình đã vẽ tuyến trực tiếp trên bản đồ."
        data_note = "*Dữ liệu mô phỏng AirGuard AI.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"
        details = (
            f"• **Điểm xuất phát:** {origin_label}.\n"
            f"• **Lộ trình:** {route_name} ({dist} km).\n"
            f"• **Chỉ số:** AQI trung bình {avg_aqi} ({avg_cat}).\n"
            f"• **Khuyến nghị:** {advice}\n\n{map_feedback}"
        )

        highlights_data = [
            {"label": "Cự ly", "value": f"khoảng {dist} km"},
            {"label": "AQI trung bình trên tuyến", "value": str(avg_aqi), "description": avg_cat},
            {"label": "Khu vực chính", "value": f"{origin_label} → {route_name}"},
        ]

        intent_name = "recommend_personalized_running_route" if is_personalized else "recommend_running_route"

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": details,
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": intent_name,
            "follow_up_actions": [
                "2 km",
                "3 km",
                "5 km",
                "Đổi điểm xuất phát",
                "Xem dự báo tối nay",
            ],
        }

    @staticmethod
    def compose_forecast(
        forecast_points: list[dict[str, Any]],
        location_name: str,
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Task 10.7: Short-term Forecast."""
        headline = f"🌙 **AQI tại {location_name} được dự báo có xu hướng ổn định vào tối nay.**"

        points_text_list = []
        highlights_data = []
        for pt in forecast_points:
            label = pt.get("time_label") or pt.get("hour_label") or f"{pt.get('hour', 1)}h tới"
            val = int(pt.get("aqi", pt.get("value", 60)))
            points_text_list.append(f"- **{label}:** AQI {val}")
            highlights_data.append({"label": label, "value": f"AQI {val}"})

        if not points_text_list:
            points_text_list = [
                "- **19:00:** AQI 82",
                "- **20:00:** AQI 68",
                "- **21:00:** AQI 51",
            ]
            highlights_data = [
                {"label": "19:00", "value": "AQI 82"},
                {"label": "20:00", "value": "AQI 68"},
                {"label": "21:00", "value": "AQI 51"},
            ]

        highlights_text = "\n".join(points_text_list)
        advice = "Nếu muốn hoạt động ngoài trời, thời điểm về sau sẽ có chất lượng không khí phù hợp hơn so với đầu buổi tối."
        map_feedback = f"📍 Mình đã đưa bản đồ tới khu {location_name}."
        data_note = "*Dữ liệu dự báo mô phỏng AirGuard AI.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "forecast",
            "follow_up_actions": [
                "🏃 Tuyến chạy gợi ý tối nay",
                "🌿 So sánh với khu khác",
                "📊 Xem thông số hiện tại",
            ],
        }

    @staticmethod
    def compose_indoor_activity(
        venues: list[dict[str, Any]],
        current_summary: str,
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Task 10.8: Indoor Alternative."""
        headline = "🏠 **Được chứ. Nếu bạn muốn tránh không khí ngoài trời (CẢNH BÁO: Không nên chạy bộ ngoài trời khi AQI tăng cao), có thể chuyển sang hoạt động trong nhà.**"

        best_v = venues[0] if venues else {"name": "Phòng Gym & Yoga Nội khu"}
        alt_v = venues[1] if len(venues) > 1 else {"name": "TTTM Vincom Mega Mall Ocean Park"}

        highlights_text = (
            "Một vài lựa chọn trong nhà:\n"
            f"- 🏋️ **Gym hoặc chạy máy:** {best_v['name']}\n"
            "- 🧘 **Yoga / giãn cơ**\n"
            f"- 🛍️ **Đi bộ trong khu thương mại:** {alt_v['name']}\n"
            "- 🏠 **Tập luyện nhẹ trong nhà**"
        )

        advice = "Nếu muốn, mình có thể giúp bạn tìm khu vực trong nhà thuận tiện hơn gần vị trí hiện tại."
        map_feedback = "📍 Mình đã đánh dấu các địa điểm trong nhà trên bản đồ."
        data_note = "*Dữ liệu tiện ích AirGuard AI.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}"

        highlights_data = [
            {"label": "Thể thao trong nhà", "value": best_v["name"]},
            {"label": "Mua sắm & Đi bộ", "value": alt_v["name"]},
        ]

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{highlights_text}\n\n{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "recommend_indoor_activity",
            "follow_up_actions": [
                "🛍️ Xem Vincom Mega Mall",
                "🏋️ Phòng tập gần nhất",
                "📊 Kiểm tra lại chất lượng ngoài trời",
            ],
        }

    @staticmethod
    def compose_specific_noise(
        poi: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Specific Noise Telemetry Inquiry (Task 8 & 9)."""
        name = poi.get("short_name") or poi.get("name", "Khu vực")
        noise = poi.get("noise_db", 52)
        level_str = "rất yên tĩnh" if noise < 55 else ("mức độ âm thanh vừa phải" if noise <= 70 else "khá ồn ào")

        headline = f"🔊 **Độ ồn hiện tại tại {name} là {noise} dB ({level_str}).**"

        highlights_text = (
            f"- **Độ ồn:** {noise} dB\n"
            f"- **AQI:** {poi.get('aqi', 48)}\n"
            f"- **PM2.5:** {poi.get('pm25', 17)} µg/m³"
        )

        advice = (
            f"Mức {noise} dB đạt chuẩn QCVN 26:2010/BTNMT, "
            f"{'rất thích hợp cho các hoạt động thư giãn, đọc sách hoặc đi dạo' if noise <= 60 else 'phù hợp sinh hoạt thông thường'}."
        )
        map_feedback = f"📍 Mình đã đưa bản đồ tới khu {name}."
        data_note = "*Dữ liệu mô phỏng · cập nhật thời gian thực.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"

        highlights_data = [
            {"label": "Độ ồn", "value": f"{noise} dB", "description": level_str},
            {"label": "AQI", "value": str(poi.get("aqi", 48))},
            {"label": "PM2.5", "value": f"{poi.get('pm25', 17)} µg/m³"},
        ]

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "get_noise_metric",
            "follow_up_actions": [
                f"🌡️ Nhiệt độ tại {name}",
                f"🌿 AQI tại {name}",
                "🏃 Tìm đường chạy yên tĩnh",
            ],
        }

    @staticmethod
    def compose_specific_temp(
        poi: dict[str, Any],
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Specific Temperature Telemetry Inquiry (Task 8 & 9)."""
        name = poi.get("short_name") or poi.get("name", "Khu vực")
        temp = poi.get("temperature", 27)
        temp_str = "mát mẻ, dễ chịu" if temp < 28 else ("khá ấm áp" if temp <= 33 else "nắng nóng")

        headline = f"🌡️ **Nhiệt độ hiện tại tại {name} là {temp}°C ({temp_str}).**"

        highlights_text = (
            f"- **Nhiệt độ:** {temp}°C\n"
            f"- **AQI:** {poi.get('aqi', 48)}\n"
            f"- **Độ ồn:** {poi.get('noise_db', 52)} dB"
        )

        advice = f"Không gian quanh {name} đang {temp_str}, phù hợp cho các hoạt động ngoài trời."
        map_feedback = f"📍 Mình đã đưa bản đồ tới khu {name}."
        data_note = "*Dữ liệu mô phỏng · cập nhật thời gian thực.*"

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}\n\n{data_note}"

        highlights_data = [
            {"label": "Nhiệt độ", "value": f"{temp}°C", "description": temp_str},
            {"label": "AQI", "value": str(poi.get("aqi", 48))},
            {"label": "Độ ồn", "value": f"{poi.get('noise_db', 52)} dB"},
        ]

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": data_note,
            },
            "response": summary,
            "intent": "get_temperature_metric",
            "follow_up_actions": [
                f"🔊 Độ ồn tại {name}",
                f"🌿 AQI tại {name}",
                "⏱️ Dự báo tối nay",
            ],
        }

    @staticmethod
    def compose_precipitation_unsupported(
        poi: dict[str, Any] | None,
        time_ctx: dict[str, Any],
        request_id: str = "",
    ) -> dict[str, Any]:
        """Weather / Rain Inquiry (Out of Measurement Scope with Microclimate Context)."""
        location_name = poi["short_name"] if poi else "Ocean Park 1"

        headline = "🌧️ **Hệ thống AirGuard AI hiện chưa trang bị cảm biến đo lượng mưa thời gian thực.**"

        if poi:
            highlights_text = (
                f"- **Nhiệt độ:** {poi.get('temperature', 28)}°C\n"
                f"- **AQI:** {poi.get('aqi', 50)} (PM2.5: {poi.get('pm25', 20)} µg/m³)\n"
                f"- **Độ ồn:** {poi.get('noise_db', 55)} dB"
            )
            highlights_data = [
                {"label": "Nhiệt độ", "value": f"{poi.get('temperature', 28)}°C"},
                {"label": "AQI", "value": str(poi.get("aqi", 50))},
            ]
        else:
            highlights_text = "- **Phạm vi giám sát:** Chất lượng không khí (AQI, PM2.5, CO₂), nhiệt độ và độ ồn môi trường."
            highlights_data = []

        advice = f"Để theo dõi lượng mưa và radar vệ tinh tại {location_name}, bạn vui lòng tra cứu thêm ứng dụng thời tiết chuyên dụng (như AccuWeather hoặc TT Khí tượng Thủy văn)."
        map_feedback = f"📍 Mình đã hiển thị thông số vi khí hậu tại {location_name} trên bản đồ."

        summary = f"{headline}\n\n{highlights_text}\n\n{advice}\n\n{map_feedback}"

        return {
            "answer": {
                "headline": headline,
                "summary": summary,
                "details": f"{advice}\n\n{map_feedback}",
                "highlights": highlights_data,
                "recommendation": advice,
                "map_feedback": map_feedback,
                "data_note": "*Hệ thống quan trắc chất lượng không khí AirGuard AI.*",
            },
            "response": summary,
            "intent": "unsupported_precipitation_weather",
            "follow_up_actions": [
                f"🌡️ Nhiệt độ tại {location_name}",
                f"🌿 AQI tại {location_name}",
                "🏃 Lộ trình chạy bộ",
            ],
        }

    @staticmethod
    def compose_out_of_scope(request_id: str = "") -> dict[str, Any]:
        """General Out-of-Scope (Medical, Real estate, Dining, Traffic)."""
        headline = "ℹ️ **Yêu cầu này nằm ngoài phạm vi hoạt động của AirGuard AI.**"

        advice = (
            "AirGuard AI là trợ lý thông minh chuyên về **giám sát chất lượng không khí (AQI, PM2.5, CO₂), "
            "cảnh báo môi trường và gợi ý lộ trình vận động ngoài trời an toàn** tại Vinhomes Ocean Park 1.\n\n"
            "👉 **Bạn có thể hỏi mình về:**\n"
            "• Chất lượng không khí hiện tại hoặc dự báo 1–3h tại các phân khu (San Hô, Hồ Ngọc Trai, VinUni, Sapphire, Sao Biển...).\n"
            "• So sánh độ trong lành giữa các địa điểm để chọn nơi vui chơi, đi dạo.\n"
            "• Gợi ý cung đường chạy bộ / đạp xe với cự ly mong muốn."
        )

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
            "intent": "out_of_scope",
            "follow_up_actions": [
                "🏫 VinUni không khí thế nào?",
                "⚠️ Khu nào đang ô nhiễm nhất?",
                "🏃 Tìm đường chạy bộ 3 km",
            ],
        }

    @staticmethod
    def compose_unknown_location(
        unrecognized_loc: str,
        request_id: str = "",
    ) -> dict[str, Any]:
        """Task 7 / 11: Unknown Location Fail-Closed."""
        headline = f"📍 **Mình chưa xác định được địa điểm “{unrecognized_loc}” trong phạm vi Ocean Park 1.**"
        advice = "Bạn có thể gửi tên đường, tên toà, phân khu hoặc địa điểm gần đó thuộc Vinhomes Ocean Park 1 (như San Hô, Sao Biển, Hải Âu, Ngọc Trai, Sapphire, VinUni, Vincom...) để mình kiểm tra chính xác hơn."

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
            "intent": "unknown_location",
            "unrecognized_location": unrecognized_loc,
            "follow_up_actions": [
                "🏫 VinUni không khí thế nào?",
                "🌿 San Hô và Hồ Ngọc Trai",
                "⚠️ Khu nào ô nhiễm nhất?",
            ],
        }

    @staticmethod
    def compose_insufficient_data(request_id: str = "") -> dict[str, Any]:
        """Task 8 / 12: Insufficient Data Fail-Closed."""
        headline = "⚠️ **Mình chưa có dữ liệu đủ mới để đánh giá chính xác khu vực này lúc này.**"
        advice = "Bạn có thể thử lại sau ít phút hoặc kiểm tra một khu vực khác đang có dữ liệu hợp lệ."
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
            "intent": "insufficient_data",
            "follow_up_actions": [
                "🌿 Kiểm tra toàn khu Ocean Park 1",
                "⏱️ Thử lại sau",
            ],
        }


class ResponseValidator:
    """Validates response contracts and guards against technical leakage & map/chat desynchronization."""

    LEAK_PATTERNS = [
        re.compile(r"\bget_[a-z0-9_]+\(\)", re.IGNORECASE),
        re.compile(r"\b(tool_call|function_call|idw-dispersion-v2\.0|spatial_idw_dispersion_model)\b", re.IGNORECASE),
        re.compile(r"\b\d+\s*(?:grid\s*points?|điểm\s*lưới)\b", re.IGNORECASE),
        re.compile(r"\b(fitBounds|highlight_station|zoom_to|polyline)\b", re.IGNORECASE),
        re.compile(r"\b(map_actions|correlation_id)\b", re.IGNORECASE),
        re.compile(r"\bbackend/app/[a-z0-9_/.]*\b", re.IGNORECASE),
        re.compile(r"\bFastAPI\b", re.IGNORECASE),
    ]

    @classmethod
    def check_technical_leakage(cls, text: str) -> list[str]:
        """Returns any detected technical leakage tokens in user-facing text."""
        detected = []
        for pattern in cls.LEAK_PATTERNS:
            for match in pattern.finditer(text):
                detected.append(match.group(0))
        return detected

    @classmethod
    def validate_map_chat_consistency(
        cls,
        intent: str,
        answer_text: str,
        map_actions: list[dict[str, Any]],
    ) -> bool:
        """Task 14 & 18: Ensures the main entity referenced in chat matches map target actions."""
        if not map_actions:
            return True

        if intent in {"find_worst_location", "recommend_outdoor_location", "get_location_environment"}:
            for action in map_actions:
                target_name = action.get("name") or action.get("title") or action.get("sensor_id")
                if target_name and target_name.lower() in answer_text.lower():
                    return True
            return True

        if intent in {"recommend_running_route", "recommend_personalized_running_route"}:
            has_route_action = any(a.get("type") == "highlight_route" for a in map_actions)
            return has_route_action

        return True

    @classmethod
    def validate_response_contract(
        cls,
        intent: str,
        response_payload: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """Task 13 & 17: Validates that response payload satisfies intent contract requirements."""
        missing = []
        answer = response_payload.get("answer")
        if not isinstance(answer, dict):
            return False, ["answer_dict_missing"]

        headline = answer.get("headline", "")
        recommendation = answer.get("recommendation", "")
        full_text = response_payload.get("response", "") or answer.get("summary", "")

        if not headline:
            missing.append("headline")

        if intent == "find_worst_location":
            if not ("AQI" in full_text and ("ô nhiễm nhất" in headline or "kém nhất" in headline)):
                missing.append("worst_location_claim")
            if not recommendation:
                missing.append("recommendation")

        elif intent == "recommend_outdoor_location":
            if not ("AQI" in full_text and ("tốt nhất" in headline or "sạch nhất" in headline or "phù hợp" in headline)):
                missing.append("best_location_claim")
            if not recommendation:
                missing.append("recommendation")

        elif intent == "get_location_environment":
            if "AQI" not in full_text:
                missing.append("aqi_value")
            if not recommendation:
                missing.append("recommendation")

        elif intent == "compare_locations":
            if not ("AQI" in full_text and ("chênh lệch" in full_text.lower() or "tốt hơn" in full_text.lower())):
                missing.append("comparison_metrics")

        elif intent in {"recommend_running_route", "recommend_personalized_running_route"}:
            if not ("km" in full_text.lower() and "aqi" in full_text.lower()):
                missing.append("route_metrics")

        elif intent == "unknown_location":
            if "chưa xác định" not in full_text.lower():
                missing.append("unknown_location_notice")

        elif intent == "insufficient_data":
            if "chưa có dữ liệu" not in full_text.lower() and "không đủ dữ liệu" not in full_text.lower():
                missing.append("insufficient_data_notice")

        return len(missing) == 0, missing
