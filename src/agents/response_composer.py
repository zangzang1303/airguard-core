from __future__ import annotations

from collections.abc import Mapping
from statistics import fmean
from typing import Any

from src.agents.policies.forecast_response import assess_forecast
from src.agents.policies.grounding import Intent, RouteDecision
from src.agents.policies.impact_assessment import assess_environmental_impact
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION, build_recommendation
from src.agents.policies.spatial_response import (
    angular_difference,
    bearing_degrees,
    get_spatial_location,
    nearest_grid_point,
)

INSUFFICIENT_DATA_MESSAGE = (
    "Không đủ dữ liệu đáng tin cậy để trả lời yêu cầu này. "
    "Hãy kiểm tra lại mã trạm và thử lại khi backend có dữ liệu valid, fresh và online."
)
SIMULATOR_NOTICE = "Đây là dữ liệu mô phỏng, không phải quan trắc chính thức."


def compose_response(
    decision: RouteDecision,
    tool_results: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if decision.direct_response is not None:
        return {"answer": decision.direct_response, "sources": [], "outcome": _direct_outcome(decision)}

    if not tool_results or any(not result.get("ok", False) for result in tool_results):
        return {"answer": INSUFFICIENT_DATA_MESSAGE, "sources": [], "outcome": "insufficient_data"}

    data_items = [result["data"] for result in tool_results]
    if not _passes_quality_gate(decision.intent, data_items):
        return {"answer": INSUFFICIENT_DATA_MESSAGE, "sources": [], "outcome": "insufficient_data"}
    if decision.comparison_mode == "highest_aqi" and any(
        item.get("aqi") is None for item in data_items[0].get("items", [])
    ):
        return {"answer": INSUFFICIENT_DATA_MESSAGE, "sources": [], "outcome": "insufficient_data"}

    composers = {
        Intent.CURRENT: lambda items: _compose_current(decision, items),
        Intent.HISTORY: _compose_history,
        Intent.COMPARE: lambda items: _compose_compare(decision, items),
        Intent.WEATHER: _compose_weather,
        Intent.FORECAST: _compose_forecast,
        Intent.ALERT: _compose_alerts,
        Intent.USER_PROFILE: _compose_profile,
        Intent.PROPOSAL: _compose_proposal_gate,
        Intent.IMPACT: _compose_impact,
    }
    if decision.intent == Intent.RECOMMENDATION:
        try:
            answer = _compose_recommendation(
                data_items,
                recommendation_window_limited=decision.recommendation_window_limited,
            )
        except ValueError:
            return {"answer": INSUFFICIENT_DATA_MESSAGE, "sources": [], "outcome": "insufficient_data"}
        return {
            "answer": answer,
            "sources": _sources(decision.intent, tool_results),
            "outcome": "answered",
            "recommendation_policy_version": RECOMMENDATION_POLICY_VERSION,
        }
    if decision.intent == Intent.SPATIAL:
        try:
            answer = _compose_spatial(decision, data_items)
        except (KeyError, TypeError, ValueError):
            return {
                "answer": INSUFFICIENT_DATA_MESSAGE,
                "sources": [],
                "outcome": "insufficient_data",
            }
        return {
            "answer": answer,
            "sources": _sources(decision.intent, tool_results),
            "outcome": "answered",
        }
    composer = composers.get(decision.intent)
    if composer is None:
        return {"answer": INSUFFICIENT_DATA_MESSAGE, "sources": [], "outcome": "insufficient_data"}
    answer = composer(data_items)
    return {"answer": answer, "sources": _sources(decision.intent, tool_results), "outcome": "answered"}


def _direct_outcome(decision: RouteDecision) -> str:
    if decision.safety_category:
        return "refused"
    if decision.refusal_category:
        return "refused"
    if decision.intent == Intent.CLARIFICATION:
        return "clarification"
    return "direct_response"


def _passes_quality_gate(intent: Intent, data_items: list[Mapping[str, Any]]) -> bool:
    if intent == Intent.CURRENT:
        return _measurement_is_usable(data_items[0])
    if intent == Intent.IMPACT:
        return _measurement_is_usable(data_items[0]) and data_items[0].get("aqi") is not None
    if intent == Intent.HISTORY:
        items = data_items[0].get("items", [])
        return bool(items) and all(
            item.get("measured_at") is not None and bool(item.get("source")) for item in items
        )
    if intent == Intent.COMPARE:
        items = data_items[0].get("items", [])
        return bool(items) and all(_measurement_is_usable(item) for item in items)
    if intent == Intent.WEATHER:
        weather = data_items[0]
        return weather.get("is_stale") is False and any(
            weather.get(field) is not None for field in ("temperature", "humidity", "wind_speed", "rainfall")
        )
    if intent == Intent.FORECAST:
        forecast = data_items[0]
        if forecast.get("is_stale") is not False or forecast.get("freshness") != "fresh":
            return False
        if forecast.get("metric") not in {"aqi", "pm25"} or not all(forecast.get(field) for field in ("generated_at", "model_name", "model_version", "source")):
            return False
        items = data_items[0].get("items", [])
        return bool(items) and all(
            bool(item.get("source"))
            and item.get("forecast_at") is not None
            and item.get("hour") is not None
            and (item.get("value") is not None or (item.get("value_min") is not None and item.get("value_max") is not None))
            for item in items
        )
    if intent == Intent.SPATIAL:
        spatial = data_items[0]
        data_quality = spatial.get("data_quality", {})
        weather = spatial.get("weather", {})
        stations_used = data_quality.get("stations_used", [])
        stations_required = data_quality.get("stations_required")
        return (
            data_quality.get("status") == "valid"
            and isinstance(stations_required, int)
            and stations_required >= 3
            and len(stations_used) >= stations_required
            and bool(spatial.get("grid_points"))
            and bool(spatial.get("station_inputs"))
            and bool(spatial.get("source"))
            and bool(spatial.get("model_version"))
            and spatial.get("timestamp") is not None
            and weather.get("is_stale") is False
            and bool(weather.get("source"))
        )
    if intent == Intent.RECOMMENDATION:
        if len(data_items) != 6:
            return False
        current, weather, forecast, alerts, profile, comparison = data_items
        return (
            _measurement_is_usable(current)
            and weather.get("is_stale") is False
            and bool(weather.get("source"))
            and bool(forecast.get("items"))
            and forecast.get("station_id") == current.get("station_id")
            and forecast.get("is_stale") is False
            and forecast.get("freshness") in (None, "fresh", "valid")
            and isinstance(alerts.get("items"), list)
            and profile.get("group") in {"normal", "sensitive", "outdoor_sport"}
            and bool(comparison.get("items"))
            and all(_measurement_is_usable(item) for item in comparison.get("items", []))
        )
    if intent == Intent.PROPOSAL:
        return _measurement_is_usable(data_items[0])
    return True


def _measurement_is_usable(data: Mapping[str, Any]) -> bool:
    return (
        data.get("pm25") is not None
        and data.get("status", "").lower() == "online"
        and data.get("is_stale") is False
    )


def _compose_current(decision: RouteDecision, data_items: list[Mapping[str, Any]]) -> str:
    data = data_items[0]
    entity_note = (
        f" Số liệu này đến từ trạm {data['station_id']}, đại diện {decision.station_entity_name}."
        if decision.station_entity_name
        else ""
    )
    if data.get("aqi") is not None:
        category = f" ({data['aqi_category']})" if data.get("aqi_category") else ""
        return (
            f"Quan sát tổng quan tại {data['station_id']}: AQI {data['aqi']:g}{category}. "
            f"Các chỉ số cùng thời điểm: PM2.5 {_format_measurement(data.get('pm25'), 'µg/m³')}; "
            f"CO₂ {_format_measurement(data.get('co2'), 'ppm')}; "
            f"tiếng ồn {_format_measurement(data.get('noise_db'), 'dB')}; "
            f"nhiệt độ {_format_measurement(data.get('temperature'), '°C')}. "
            f"Cập nhật {data['updated_at']}; trạng thái {data['status']}; nguồn {data['source']}."
            f"{entity_note} {SIMULATOR_NOTICE}"
        )
    level = f", mức backend: {data['level']}" if data.get("level") else ""
    return (
        f"Quan sát tại {data['station_id']}: PM2.5 {data['pm25']:g} µg/m³ lúc {data['updated_at']}"
        f"; trạng thái {data['status']}{level}. Nguồn: {data['source']}.{entity_note} {SIMULATOR_NOTICE}"
    )


def _format_measurement(value: Any, unit: str) -> str:
    return f"{float(value):g} {unit}" if value is not None else "không khả dụng"


def _compose_impact(data_items: list[Mapping[str, Any]]) -> str:
    data = data_items[0]
    assessment = assess_environmental_impact(data)
    contributors = "; ".join(assessment.contributors)
    return (
        f"Đánh giá mức độ ảnh hưởng tại {data['station_id']}: {assessment.label}. "
        f"{assessment.summary} Căn cứ cùng request: {contributors}. "
        f"Thời điểm {data['updated_at']}; nguồn {data['source']}; policy {assessment.policy_version}. "
        f"Đây là đánh giá vận hành từ dữ liệu simulator, không phải chẩn đoán sức khỏe hay cảnh báo khẩn cấp."
    )


def _compose_history(data_items: list[Mapping[str, Any]]) -> str:
    data = data_items[0]
    items = data["items"]
    values = [item["pm25"] for item in items]
    first = items[0]
    last = items[-1]
    return (
        f"Dữ liệu lịch sử {data['station_id']} có {len(items)} điểm từ {first['measured_at']} đến "
        f"{last['measured_at']}. Suy luận từ chính các điểm này: PM2.5 thấp nhất {min(values):g}, "
        f"cao nhất {max(values):g}, trung bình {fmean(values):.1f} µg/m³. "
        f"Nguồn: {first['source']}. {SIMULATOR_NOTICE}"
    )


def _compose_compare(decision: RouteDecision, data_items: list[Mapping[str, Any]]) -> str:
    items = data_items[0]["items"]
    if decision.comparison_mode == "highest_aqi":
        highest = max(items, key=lambda item: float(item["aqi"]))
        return (
            f"Theo so sánh AQI cùng request, {highest['station_id']} cao nhất: AQI {highest['aqi']:g} "
            f"lúc {highest['updated_at']} (nguồn {highest['source']}). {SIMULATOR_NOTICE}"
        )
    observations = "; ".join(
        f"{item['station_id']} = {item['pm25']:g} µg/m³ lúc {item['updated_at']} (nguồn {item['source']})"
        for item in items
    )
    return f"So sánh các quan sát cùng request: {observations}. {SIMULATOR_NOTICE}"


def _compose_weather(data_items: list[Mapping[str, Any]]) -> str:
    data = data_items[0]
    labels = {
        "temperature": "nhiệt độ",
        "humidity": "độ ẩm",
        "wind_speed": "tốc độ gió",
        "rainfall": "lượng mưa",
    }
    values = ", ".join(f"{labels[field]} {data[field]:g}" for field in labels if data.get(field) is not None)
    fallback_notice = (
        " Đây là weather fallback được gắn nhãn, không phải dữ liệu weather live/official."
        if data["is_fallback"]
        else ""
    )
    return (
        f"Bối cảnh thời tiết tại {data['area_id']} lúc {data['observed_at']}: {values}. "
        f"Nguồn: {data['source']}.{fallback_notice} {SIMULATOR_NOTICE}"
    )


def _compose_forecast(data_items: list[Mapping[str, Any]]) -> str:
    data = data_items[0]
    assessment = assess_forecast(dict(data))
    points = []
    for item in data["items"]:
        horizon = item.get("forecast_at") or f"+{item.get('hour')} giờ"
        unit = "AQI" if data["metric"] == "aqi" else "µg/m³"
        if item.get("value") is not None:
            value = f"{item['value']:g} {unit}"
        else:
            value = f"{item.get('value_min'):g}-{item.get('value_max'):g} {unit}"
        confidence = f", confidence {item['confidence']:.0%}" if item.get("confidence") is not None else ""
        source = f", nguồn {item['source']}" if item.get("source") else ""
        points.append(f"{horizon}: {value}{confidence}{source}")
    metadata = []
    if assessment.generated_at:
        metadata.append(f"tạo lúc {assessment.generated_at}")
    if assessment.model_name:
        metadata.append(f"mô hình {assessment.model_name} ({data['model_version']})")
    metadata.extend([f"nguồn {data['source']}", f"freshness {data['freshness']}"])
    metadata.append(f"confidence {assessment.confidence_label}")
    limitation = f" Giới hạn: {'; '.join(assessment.limitations)}." if assessment.limitations else ""
    return (
        f"Dự báo {data['metric'].upper()} cho {data['station_id']} (không phải quan sát hiện tại): {'; '.join(points)}. "
        f"Metadata: {', '.join(metadata)}. Xu hướng: {assessment.trend}. "
        f"{SIMULATOR_NOTICE}{limitation}"
    )


def _compose_alerts(data_items: list[Mapping[str, Any]]) -> str:
    items = data_items[0]["items"]
    if not items:
        return "Backend không trả về cảnh báo active nào cho bộ lọc trong request này."
    alerts = "; ".join(
        f"{item['alert_id']} tại {item['station_id']} ({item['alert_type']}): severity {item['severity']}, "
        f"observed {_format_alert_value(item.get('observed_value'), item.get('unit'))}, "
        f"threshold {_format_alert_value(item.get('threshold_value'), item.get('unit'))}, "
        f"khuyến nghị {item.get('recommendation') or 'theo dõi theo quy trình vận hành'}, tạo lúc {item['created_at']}"
        for item in items
    )
    return f"Cảnh báo active từ backend: {alerts}. {SIMULATOR_NOTICE}"


def _format_alert_value(value: Any, unit: Any) -> str:
    if value is None:
        return "không có số đo"
    return f"{float(value):g}{(' ' + str(unit)) if unit else ''}"


def _compose_profile(data_items: list[Mapping[str, Any]]) -> str:
    data = data_items[0]
    return f"Backend xác nhận nhóm hồ sơ người dùng là {data['group']}."


def _compose_proposal_gate(data_items: list[Mapping[str, Any]]) -> str:
    station_id = data_items[0]["station_id"]
    return (
        f"Đã kiểm tra evidence backend cho {station_id}. AI-002 chưa tạo warning proposal; bước tạo chỉ được "
        "thực hiện sau cổng eligibility của AI-005 và mọi proposal vẫn phải ở trạng thái pending để manager review."
    )


def _compose_recommendation(
    data_items: list[Mapping[str, Any]], *, recommendation_window_limited: bool = False
) -> str:
    current, weather, forecast, alerts, profile, comparison = (dict(item) for item in data_items)
    decision, assessment = build_recommendation(
        current=current,
        alerts=alerts,
        forecast=forecast,
        profile=profile,
        comparison=comparison,
    )
    forecast_points = []
    for item in forecast["items"]:
        horizon = item.get("forecast_at") or f"+{item.get('hour')} giờ"
        if item.get("value") is not None:
            value = f"{item['value']:g} µg/m³"
        elif item.get("value_min") is not None and item.get("value_max") is not None:
            value = f"{item['value_min']:g}-{item['value_max']:g} µg/m³"
        elif item.get("pm25") is not None:
            value = f"{item['pm25']:g} µg/m³"
        else:
            value = f"{item['pm25_min']:g}-{item['pm25_max']:g} µg/m³"
        forecast_points.append(f"{horizon}: {value} (nguồn {item['source']})")

    weather_values = []
    for field, label in (
        ("temperature", "nhiệt độ"),
        ("humidity", "độ ẩm"),
        ("wind_speed", "tốc độ gió"),
        ("rainfall", "lượng mưa"),
    ):
        if weather.get(field) is not None:
            weather_values.append(f"{label} {weather[field]:g}")

    alert_note = "có cảnh báo active cùng trạm" if decision.has_active_alert else "không có cảnh báo active cùng trạm"
    limitation = f" Giới hạn dự báo: {'; '.join(assessment.limitations)}." if assessment.limitations else ""
    time_scope = (
        " AirGuard không có đủ contract để đánh giá toàn bộ hôm nay; thời điểm phù hợp chỉ được chọn "
        "trong cửa sổ forecast baseline 1–3 giờ ở trên."
        if recommendation_window_limited
        else ""
    )
    return (
        f"Quan sát tại {current['station_id']}: PM2.5 {current['pm25']:g} µg/m³ lúc {current['updated_at']}, "
        f"mức backend {decision.pm25_band}, nguồn {current['source']}; {alert_note}. "
        f"Bối cảnh thời tiết lúc {weather['observed_at']}: {', '.join(weather_values)}, nguồn {weather['source']}. "
        f"Dự báo (không phải quan sát hiện tại): {'; '.join(forecast_points)}; confidence "
        f"{assessment.confidence_label}, xu hướng {assessment.trend}. "
        f"Khuyến nghị cho nhóm {decision.user_group}: {decision.action} "
        f"Cơ sở: {'; '.join(decision.rationale)}. Policy: {decision.policy_version}. "
        f"{SIMULATOR_NOTICE}{limitation}{time_scope}"
    )


def _compose_spatial(
    decision: RouteDecision,
    data_items: list[Mapping[str, Any]],
) -> str:
    data = data_items[0]
    grid_points = data["grid_points"]
    unit = data["unit"]
    samples = []
    for location_id in decision.spatial_location_ids:
        location = get_spatial_location(location_id)
        point, distance_km = nearest_grid_point(location, grid_points)
        samples.append(
            {
                "location": location,
                "point": point,
                "distance_km": distance_km,
            }
        )

    time_label = (
        f"mốc dự báo +{data['forecast_hour']} giờ"
        if data["forecast_hour"] > 0
        else "mốc hiện tại"
    )
    provenance = (
        f"Lưới {data['model_version']} lúc {data['timestamp']}, nguồn {data['source']}; "
        f"gió từ {data['weather']['source']}"
    )

    if decision.spatial_analysis == "wind" and decision.spatial_origin_id:
        origin = get_spatial_location(decision.spatial_origin_id)
        target_samples = [
            sample
            for sample in samples
            if sample["location"].location_id != origin.location_id
            and sample["location"].category == "residential"
        ]
        if not target_samples:
            raise ValueError("wind analysis requires at least one residential target")
        wind_direction = float(data["weather"]["wind_direction_deg"])
        ranked_targets = sorted(
            target_samples,
            key=lambda sample: angular_difference(
                bearing_degrees(origin, sample["location"]),
                wind_direction,
            ),
        )
        best = ranked_targets[0]
        target = best["location"]
        target_bearing = bearing_degrees(origin, target)
        direction_delta = angular_difference(target_bearing, wind_direction)
        if direction_delta <= 45:
            alignment = "phù hợp rõ với hướng xuôi gió"
        elif direction_delta <= 90:
            alignment = "phù hợp một phần với hướng xuôi gió"
        else:
            alignment = "không nằm rõ trên trục xuôi gió"
        point = best["point"]
        return (
            f"Theo quy ước vector của mô hình, gió hướng {wind_direction:g}° với tốc độ "
            f"{data['weather']['wind_speed_ms']:g} m/s. Từ {origin.name}, {target.name} là điểm dân cư "
            f"có hướng gần vector gió nhất trong catalog ({alignment}, lệch {direction_delta:.1f}°). "
            f"Giá trị nội suy tại điểm lưới gần {target.name} là {point['value']:g} {unit}, "
            f"mức {point['level']}, ở {time_label}. Đây là suy luận hình học từ grid và vector gió, "
            f"không phải khẳng định nguồn phát thải hay mô hình lan truyền vật lý. {provenance}. "
            f"{SIMULATOR_NOTICE}"
        )

    if samples:
        observations = "; ".join(
            f"{sample['location'].name} ≈ {sample['point']['value']:g} {unit} "
            f"(mức {sample['point']['level']}, điểm lưới cách {sample['distance_km']:.2f} km)"
            for sample in samples
        )
        highest = max(samples, key=lambda sample: float(sample["point"]["value"]))
        lowest = min(samples, key=lambda sample: float(sample["point"]["value"]))
        comparison = ""
        if len(samples) >= 2:
            comparison = (
                f" Trong các vị trí này, {highest['location'].name} cao nhất và "
                f"{lowest['location'].name} thấp nhất theo grid cùng request."
            )
        return (
            f"Ước tính nội suy không gian ở {time_label}: {observations}.{comparison} "
            f"{provenance}. Đây là suy luận không gian từ điểm lưới IDW gần nhất, không phải trạm đo đặt tại từng POI. "
            f"{SIMULATOR_NOTICE}"
        )

    values = [float(point["value"]) for point in grid_points]
    return (
        f"Bản đồ nội suy {data['metric']} ở {time_label} có khoảng giá trị "
        f"{min(values):g}-{max(values):g} {unit} trên {len(grid_points)} điểm lưới. "
        f"{provenance}. {data['disclaimer']}"
    )


def _sources(intent: Intent, tool_results: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for result in tool_results:
        data = result["data"]
        tool_name = result["tool_name"]
        if tool_name == "get_station_history":
            for item in data.get("items", []):
                sources.append(
                    {
                        "tool_name": tool_name,
                        "station_id": item.get("station_id"),
                        "observed_at": item.get("measured_at"),
                        "source": item.get("source"),
                    }
                )
        elif tool_name == "compare_stations":
            for item in data.get("items", []):
                sources.append(_measurement_source(tool_name, item))
        elif tool_name == "get_active_alerts":
            for item in data.get("items", []):
                sources.append(
                    {
                        "tool_name": tool_name,
                        "station_id": item.get("station_id"),
                        "observed_at": item.get("created_at"),
                        "source": item.get("source"),
                    }
                )
        elif tool_name == "get_pm25_forecast":
            for item in data.get("items", []):
                sources.append(
                    {
                        "tool_name": tool_name,
                        "station_id": data.get("station_id"),
                        "observed_at": item.get("forecast_at") or f"+{item.get('hour')}h",
                        "source": item.get("source"),
                    }
                )
        elif tool_name == "get_weather_context":
            sources.append(
                {
                    "tool_name": tool_name,
                    "observed_at": data.get("observed_at"),
                    "source": data.get("source"),
                }
            )
        elif tool_name == "get_user_profile":
            # The profile is a same-request policy input.  Do not expose its
            # user id in sources, but make its backend authority visible.
            sources.append(
                {
                    "tool_name": tool_name,
                    "observed_at": None,
                    "source": "backend_user_profile",
                }
            )
        elif tool_name == "get_spatial_air_quality":
            sources.append(
                {
                    "tool_name": tool_name,
                    "observed_at": data.get("timestamp"),
                    "source": data.get("source"),
                }
            )
        elif tool_name == "get_current_pm25" and data.get("station_id"):
            sources.append(_measurement_source(tool_name, data))
    return sources


def _measurement_source(tool_name: str, item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "station_id": item.get("station_id"),
        "observed_at": item.get("updated_at"),
        "source": item.get("source"),
    }
