from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from src.agents.policies.forecast_response import (
    ForecastAssessment,
    assess_forecast,
    forecast_is_fresh,
    forecast_value,
)

RECOMMENDATION_POLICY_VERSION = "2026-08-19.ai-003.v2"

UserGroup = Literal["normal", "sensitive", "outdoor_sport"]
Pm25Band = Literal["good", "moderate", "unhealthy_sensitive", "unhealthy", "very_unhealthy", "hazardous"]


@dataclass(frozen=True)
class RecommendationDecision:
    user_group: UserGroup
    pm25_band: Pm25Band
    forecast_trend: str
    has_active_alert: bool
    action: str
    rationale: tuple[str, ...]
    best_station_id: str | None = None
    best_station_aqi: int | None = None
    best_station_pm25: float | None = None
    best_window_label: str | None = None
    best_window_pm25: float | None = None
    policy_version: str = RECOMMENDATION_POLICY_VERSION


_ACTIONS: dict[Pm25Band, dict[UserGroup, str]] = {
    "good": {
        "normal": "Có thể cân nhắc hoạt động ngoài trời như thường lệ và tiếp tục theo dõi AirGuard.",
        "sensitive": "Có thể cân nhắc hoạt động nhẹ ngoài trời; dừng lại nếu cảm thấy không thoải mái.",
        "outdoor_sport": "Có thể cân nhắc tập luyện ngoài trời và tiếp tục theo dõi số liệu trước buổi tập.",
    },
    "moderate": {
        "normal": "Có thể hoạt động ngoài trời nhưng nên theo dõi cập nhật PM2.5 tiếp theo.",
        "sensitive": "Nên giảm thời lượng hoạt động ngoài trời và ưu tiên khu vực ít phơi nhiễm hơn.",
        "outdoor_sport": "Nên giảm cường độ hoặc thời lượng tập luyện ngoài trời và theo dõi cập nhật mới.",
    },
    "unhealthy_sensitive": {
        "normal": "Có thể hoạt động ngoài trời ở mức vừa phải nhưng nên theo dõi cập nhật tiếp theo.",
        "sensitive": "Nên hạn chế ra ngoài và ưu tiên ở trong nhà tại khu vực này.",
        "outdoor_sport": "Nên giảm cường độ buổi tập hoặc dời sang khung giờ có dự báo tốt hơn.",
    },
    "unhealthy": {
        "normal": "Nên giảm hoạt động ngoài trời kéo dài tại khu vực này.",
        "sensitive": "Nên tránh hoạt động ngoài trời kéo dài tại khu vực này và chọn không gian trong nhà.",
        "outdoor_sport": "Nên hoãn buổi tập ngoài trời hoặc chuyển sang tập trong nhà.",
    },
    "very_unhealthy": {
        "normal": "Nên tránh hoạt động ngoài trời tại khu vực này trong thời điểm hiện tại.",
        "sensitive": "Nên tránh khu vực này và hạn chế phơi nhiễm ngoài trời.",
        "outdoor_sport": "Nên hoãn hoạt động thể thao ngoài trời và chọn phương án trong nhà.",
    },
    "hazardous": {
        "normal": "Nên ở trong nhà và tránh mọi hoạt động ngoài trời tại khu vực này.",
        "sensitive": "Nên ở trong nhà và tránh hoàn toàn phơi nhiễm ngoài trời tại khu vực này.",
        "outdoor_sport": "Nên hủy hoạt động thể thao ngoài trời và chỉ tập trong nhà.",
    },
}

# The sensitive group is warned before the general population: as soon as the
# backend band leaves "good" it also gets the indoor-protection advice.
_SENSITIVE_INDOOR_ADVICE = (
    "Cảnh báo sớm cho nhóm nhạy cảm: nên đóng cửa sổ và bật máy lọc không khí trong nhà."
)


def build_recommendation(
    *,
    current: dict[str, Any],
    alerts: dict[str, Any],
    forecast: dict[str, Any],
    profile: dict[str, Any],
    comparison: dict[str, Any] | None = None,
) -> tuple[RecommendationDecision, ForecastAssessment]:
    station_id = str(current.get("station_id") or "")
    if not station_id or current.get("pm25") is None:
        raise ValueError("recommendation requires a current measurement")
    if str(current.get("status", "")).lower() != "online" or current.get("is_stale") is not False:
        raise ValueError("recommendation requires fresh online data")

    group = profile.get("group")
    if group not in {"normal", "sensitive", "outdoor_sport"}:
        raise ValueError("recommendation requires a supported backend user group")

    band = _pm25_band(current)
    assessment = assess_forecast(forecast, current=current)
    if not forecast_is_fresh(assessment):
        raise ValueError("recommendation requires a fresh forecast")

    active_alerts = [
        item
        for item in alerts.get("items", [])
        if item.get("station_id") == station_id and str(item.get("status", "")).lower() == "active"
    ]
    has_active_alert = bool(active_alerts)

    rationale = [f"backend phân loại PM2.5 hiện tại ở mức {band}"]
    if has_active_alert:
        rationale.append("backend đang có cảnh báo active cho cùng trạm")
    if assessment.trend == "increasing":
        rationale.append("dự báo hợp lệ cho thấy xu hướng tăng")
    elif assessment.trend == "decreasing":
        rationale.append("dự báo hợp lệ cho thấy xu hướng giảm")
    elif assessment.trend == "stable":
        rationale.append("dự báo hợp lệ cho thấy xu hướng tương đối ổn định")
    else:
        rationale.append("confidence dự báo thấp nên không dùng xu hướng để khẳng định")

    action = _ACTIONS[band][group]
    if has_active_alert and band in {"good", "moderate"}:
        action = f"Do có cảnh báo active, {action[0].lower()}{action[1:]}"
    if assessment.trend == "increasing" and band in {"good", "moderate"}:
        action = f"Do dự báo có xu hướng tăng, {action[0].lower()}{action[1:]}"

    best_station_id: str | None = None
    best_station_aqi: int | None = None
    best_station_pm25: float | None = None
    best_window_label: str | None = None
    best_window_pm25: float | None = None

    if group == "sensitive" and band != "good":
        action = f"{action} {_SENSITIVE_INDOOR_ADVICE}"

    if group == "outdoor_sport":
        best_station_id, best_station_aqi, best_station_pm25 = _best_station(comparison)
        best_window_label, best_window_pm25 = _best_forecast_window(forecast)
        action = (
            f"{action} Trong snapshot hiện tại, ưu tiên khu vực trạm {best_station_id} "
            f"(AQI {best_station_aqi}, PM2.5 {best_station_pm25:g} µg/m³). "
            f"Tại trạm {station_id}, khung dự báo phù hợp nhất là {best_window_label} "
            f"với PM2.5 khoảng {best_window_pm25:g} µg/m³."
        )
        rationale.append("đã đối chiếu snapshot fresh của 5 trạm trong cùng request")
        rationale.append("đã chọn điểm dự báo PM2.5 thấp nhất tại trạm đang hỏi")

    return (
        RecommendationDecision(
            user_group=group,
            pm25_band=band,
            forecast_trend=assessment.trend,
            has_active_alert=has_active_alert,
            action=action,
            rationale=tuple(rationale),
            best_station_id=best_station_id,
            best_station_aqi=best_station_aqi,
            best_station_pm25=best_station_pm25,
            best_window_label=best_window_label,
            best_window_pm25=best_window_pm25,
        ),
        assessment,
    )


def _pm25_band(current: dict[str, Any]) -> Pm25Band:
    level = str(current.get("level") or "").lower()
    aliases: dict[str, Pm25Band] = {
        "good": "good",
        "moderate": "moderate",
        "unhealthy_sensitive": "unhealthy_sensitive",
        "unhealthy-sensitive": "unhealthy_sensitive",
        "unhealthy for sensitive groups": "unhealthy_sensitive",
        "unhealthy": "unhealthy",
        "very_unhealthy": "very_unhealthy",
        "very-unhealthy": "very_unhealthy",
        "very unhealthy": "very_unhealthy",
        "hazardous": "hazardous",
    }
    if level not in aliases:
        raise ValueError("recommendation requires a backend PM2.5 level")
    return aliases[level]


def _best_station(comparison: dict[str, Any] | None) -> tuple[str, int, float]:
    items = comparison.get("items", []) if comparison else []
    candidates = [
        item
        for item in items
        if item.get("station_id")
        and item.get("aqi") is not None
        and item.get("pm25") is not None
        and str(item.get("status", "")).lower() == "online"
        and item.get("is_stale") is False
    ]
    if len(candidates) < 2:
        raise ValueError("outdoor recommendation requires fresh station comparison")
    best = min(candidates, key=lambda item: (float(item["aqi"]), float(item["pm25"])))
    return str(best["station_id"]), int(best["aqi"]), float(best["pm25"])


def _best_forecast_window(forecast: dict[str, Any]) -> tuple[str, float]:
    candidates = [
        (item, value)
        for item in forecast.get("items", [])
        if (value := forecast_value(item)) is not None
    ]
    if not candidates:
        raise ValueError("outdoor recommendation requires forecast values")
    item, value = min(candidates, key=lambda candidate: candidate[1])
    label = str(item.get("forecast_at") or f"+{item.get('hour')} giờ")
    return label, float(value)
