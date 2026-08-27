from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

IMPACT_POLICY_VERSION = "2026-08-13.impact-v1"
ImpactLevel = Literal["low", "moderate", "high", "very_high"]


@dataclass(frozen=True)
class ImpactAssessment:
    level: ImpactLevel
    label: str
    summary: str
    contributors: tuple[str, ...]
    policy_version: str = IMPACT_POLICY_VERSION


def assess_environmental_impact(current: Mapping[str, Any]) -> ImpactAssessment:
    """Classify operational environmental impact from one validated station snapshot.

    AQI is the primary signal. CO₂, noise and temperature can add transparent context,
    but may not raise a missing AQI snapshot into a health or emergency claim.
    """
    aqi = current.get("aqi")
    pm25 = current.get("pm25")
    if aqi is None or pm25 is None:
        raise ValueError("impact assessment requires AQI and PM2.5 evidence")

    aqi = float(aqi)
    if aqi <= 50:
        level, label, summary = "low", "Thấp", "Điều kiện AQI hiện tại có tác động vận hành thấp."
    elif aqi <= 100:
        level, label, summary = "moderate", "Trung bình", "AQI cần được theo dõi trong hoạt động ngoài trời thông thường."
    elif aqi <= 150:
        level, label, summary = "high", "Cao", "AQI là yếu tố chính làm tăng mức ảnh hưởng của khu vực."
    else:
        level, label, summary = "very_high", "Rất cao", "AQI là yếu tố chính cần được ưu tiên theo dõi và xử lý theo quy trình."

    contributors = [f"AQI {aqi:g} là chỉ số tổng quan chính"]
    co2 = current.get("co2")
    if co2 is not None:
        contributors.append(
            f"CO₂ {float(co2):g} ppm " + ("cần theo dõi bổ sung" if float(co2) >= 1000 else "đang ở mức tham chiếu của trạm")
        )
    noise = current.get("noise_db")
    if noise is not None:
        contributors.append(
            f"tiếng ồn {float(noise):g} dB " + ("là yếu tố gây nhiễu đáng chú ý" if float(noise) >= 75 else "được ghi nhận để theo dõi")
        )
    temperature = current.get("temperature")
    if temperature is not None:
        contributors.append(
            f"nhiệt độ {float(temperature):g} °C " + ("làm tăng nhu cầu theo dõi điều kiện ngoài trời" if float(temperature) >= 35 else "là ngữ cảnh môi trường")
        )
    return ImpactAssessment(level=level, label=label, summary=summary, contributors=tuple(contributors))
