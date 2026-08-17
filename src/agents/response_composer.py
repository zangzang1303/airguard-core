from __future__ import annotations

from collections.abc import Mapping
from statistics import fmean
from typing import Any

from src.agents.policies.forecast_response import assess_forecast
from src.agents.policies.grounding import Intent, RouteDecision
from src.agents.policies.impact_assessment import IMPACT_POLICY_VERSION, assess_environmental_impact
from src.agents.policies.recommendations import RECOMMENDATION_POLICY_VERSION, build_recommendation

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

    composers = {
        Intent.CURRENT: _compose_current,
        Intent.HISTORY: _compose_history,
        Intent.COMPARE: _compose_compare,
        Intent.WEATHER: _compose_weather,
        Intent.FORECAST: _compose_forecast,
        Intent.ALERT: _compose_alerts,
        Intent.USER_PROFILE: _compose_profile,
        Intent.PROPOSAL: _compose_proposal_gate,
        Intent.IMPACT: _compose_impact,
    }
    if decision.intent == Intent.RECOMMENDATION:
        try:
            answer = _compose_recommendation(data_items)
        except ValueError:
            return {"answer": INSUFFICIENT_DATA_MESSAGE, "sources": [], "outcome": "insufficient_data"}
        return {
            "answer": answer,
            "sources": _sources(decision.intent, tool_results),
            "outcome": "answered",
            "recommendation_policy_version": RECOMMENDATION_POLICY_VERSION,
        }
    composer = composers.get(decision.intent)
    if composer is None:
        return {"answer": INSUFFICIENT_DATA_MESSAGE, "sources": [], "outcome": "insufficient_data"}
    answer = composer(data_items)
    return {"answer": answer, "sources": _sources(decision.intent, tool_results), "outcome": "answered"}


def _direct_outcome(decision: RouteDecision) -> str:
    if decision.safety_category:
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
        if forecast.get("is_stale") is not False:
            return False
        if forecast.get("freshness") not in (None, "fresh", "valid"):
            return False
        items = data_items[0].get("items", [])
        return bool(items) and all(
            bool(item.get("source"))
            and (item.get("forecast_at") is not None or item.get("hour") is not None)
            and (
                item.get("pm25") is not None
                or (item.get("pm25_min") is not None and item.get("pm25_max") is not None)
            )
            for item in items
        )
    if intent == Intent.RECOMMENDATION:
        if len(data_items) != 5:
            return False
        current, weather, forecast, alerts, profile = data_items
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


def _compose_current(data_items: list[Mapping[str, Any]]) -> str:
    data = data_items[0]
    if data.get("aqi") is not None:
        category = f" ({data['aqi_category']})" if data.get("aqi_category") else ""
        return (
            f"Quan sát tổng quan tại {data['station_id']}: AQI {data['aqi']:g}{category}. "
            f"Các chỉ số cùng thời điểm: PM2.5 {_format_measurement(data.get('pm25'), 'µg/m³')}; "
            f"CO₂ {_format_measurement(data.get('co2'), 'ppm')}; "
            f"tiếng ồn {_format_measurement(data.get('noise_db'), 'dB')}; "
            f"nhiệt độ {_format_measurement(data.get('temperature'), '°C')}. "
            f"Cập nhật {data['updated_at']}; trạng thái {data['status']}; nguồn {data['source']}. {SIMULATOR_NOTICE}"
        )
    level = f", mức backend: {data['level']}" if data.get("level") else ""
    return (
        f"Quan sát tại {data['station_id']}: PM2.5 {data['pm25']:g} µg/m³ lúc {data['updated_at']}"
        f"; trạng thái {data['status']}{level}. Nguồn: {data['source']}. {SIMULATOR_NOTICE}"
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


def _compose_compare(data_items: list[Mapping[str, Any]]) -> str:
    items = data_items[0]["items"]
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
        if item.get("pm25") is not None:
            value = f"{item['pm25']:g} µg/m³"
        else:
            value = f"{item.get('pm25_min'):g}-{item.get('pm25_max'):g} µg/m³"
        confidence = f", confidence {item['confidence']:.0%}" if item.get("confidence") is not None else ""
        source = f", nguồn {item['source']}" if item.get("source") else ""
        points.append(f"{horizon}: {value}{confidence}{source}")
    metadata = []
    if assessment.generated_at:
        metadata.append(f"tạo lúc {assessment.generated_at}")
    if assessment.model_name:
        metadata.append(f"mô hình {assessment.model_name}")
    metadata.append(f"confidence {assessment.confidence_label}")
    limitation = f" Giới hạn: {'; '.join(assessment.limitations)}." if assessment.limitations else ""
    return (
        f"Dự báo PM2.5 cho {data['station_id']} (không phải quan sát hiện tại): {'; '.join(points)}. "
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


def _compose_recommendation(data_items: list[Mapping[str, Any]]) -> str:
    current, weather, forecast, alerts, profile = (dict(item) for item in data_items)
    decision, assessment = build_recommendation(
        current=current,
        alerts=alerts,
        forecast=forecast,
        profile=profile,
    )
    forecast_points = []
    for item in forecast["items"]:
        horizon = item.get("forecast_at") or f"+{item.get('hour')} giờ"
        value = (
            f"{item['pm25']:g} µg/m³"
            if item.get("pm25") is not None
            else f"{item['pm25_min']:g}-{item['pm25_max']:g} µg/m³"
        )
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
    return (
        f"Quan sát tại {current['station_id']}: PM2.5 {current['pm25']:g} µg/m³ lúc {current['updated_at']}, "
        f"mức backend {decision.pm25_band}, nguồn {current['source']}; {alert_note}. "
        f"Bối cảnh thời tiết lúc {weather['observed_at']}: {', '.join(weather_values)}, nguồn {weather['source']}. "
        f"Dự báo (không phải quan sát hiện tại): {'; '.join(forecast_points)}; confidence "
        f"{assessment.confidence_label}, xu hướng {assessment.trend}. "
        f"Khuyến nghị cho nhóm {decision.user_group}: {decision.action} "
        f"Cơ sở: {'; '.join(decision.rationale)}. Policy: {decision.policy_version}. "
        f"{SIMULATOR_NOTICE}{limitation}"
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
