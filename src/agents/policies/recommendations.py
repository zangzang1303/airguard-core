from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from src.agents.policies.forecast_response import ForecastAssessment, assess_forecast, forecast_is_fresh

RECOMMENDATION_POLICY_VERSION = "2026-08-08.ai-003.v1"

UserGroup = Literal["normal", "sensitive", "outdoor_sport"]
Pm25Band = Literal["good", "moderate", "unhealthy", "very_unhealthy"]


@dataclass(frozen=True)
class RecommendationDecision:
    user_group: UserGroup
    pm25_band: Pm25Band
    forecast_trend: str
    has_active_alert: bool
    action: str
    rationale: tuple[str, ...]
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
}


def build_recommendation(
    *,
    current: dict[str, Any],
    alerts: dict[str, Any],
    forecast: dict[str, Any],
    profile: dict[str, Any],
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

    return (
        RecommendationDecision(
            user_group=group,
            pm25_band=band,
            forecast_trend=assessment.trend,
            has_active_alert=has_active_alert,
            action=action,
            rationale=tuple(rationale),
        ),
        assessment,
    )


def _pm25_band(current: dict[str, Any]) -> Pm25Band:
    level = str(current.get("level") or "").lower()
    aliases: dict[str, Pm25Band] = {
        "good": "good",
        "moderate": "moderate",
        "unhealthy": "unhealthy",
        "very_unhealthy": "very_unhealthy",
        "very-unhealthy": "very_unhealthy",
    }
    if level not in aliases:
        raise ValueError("recommendation requires a backend PM2.5 level")
    return aliases[level]
