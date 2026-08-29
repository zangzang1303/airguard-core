from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from .database import ServiceError

REPORT_SCHEMA_VERSION = "b7-esg-reports-v1"
DEFAULT_REPORT_POLICY_VERSION = REPORT_SCHEMA_VERSION
GOOD_HOUR_POLICY_VERSION = "internal-good-hour-v1"
REFERENCE_POLICY_VERSION = "qcvn05-2023-effective-2026_who2021-v1"
ESG_FORMULA_VERSION = "estimated-device-impact-v1"
ENERGY_BASELINE_VERSION = "boost_baseline_v1"
MATRIX_COLOR_SCALE_VERSION = "pm25-fixed-scale-v1"
MATRIX_COLOR_STOPS = (0.0, 15.0, 35.0, 45.0, 75.0, 150.0)
GOOD_HOUR_PM25_THRESHOLD = 35.0
GOOD_HOUR_TARGET_RATIO = 0.85


@dataclass(frozen=True)
class ReportPolicy:
    report_policy_version: str = DEFAULT_REPORT_POLICY_VERSION
    expected_sample_interval_seconds: int = 10
    minimum_coverage_ratio: float = 0.75
    matrix_min_eligible_stations: int = 3
    good_hour_policy_version: str = GOOD_HOUR_POLICY_VERSION
    good_hour_target_ratio: float = GOOD_HOUR_TARGET_RATIO
    reference_policy_version: str = REFERENCE_POLICY_VERSION
    esg_formula_version: str = ESG_FORMULA_VERSION
    matrix_color_scale_version: str = MATRIX_COLOR_SCALE_VERSION

    def __post_init__(self) -> None:
        if not self.report_policy_version.strip():
            raise ValueError("report_policy_version must not be empty")
        if not 1 <= self.expected_sample_interval_seconds <= 3600:
            raise ValueError("expected_sample_interval_seconds must be between 1 and 3600")
        if not 0 < self.minimum_coverage_ratio <= 1:
            raise ValueError("minimum_coverage_ratio must be greater than 0 and at most 1")
        if not 1 <= self.matrix_min_eligible_stations <= 5:
            raise ValueError("matrix_min_eligible_stations must be between 1 and 5")

    def snapshot(self) -> dict[str, object]:
        return asdict(self)


def report_policy_from_environment() -> ReportPolicy:
    try:
        return ReportPolicy(
            report_policy_version=os.getenv(
                "REPORT_POLICY_VERSION", DEFAULT_REPORT_POLICY_VERSION
            ).strip(),
            expected_sample_interval_seconds=int(
                os.getenv("REPORT_EXPECTED_SAMPLE_INTERVAL_SECONDS", "10")
            ),
            minimum_coverage_ratio=float(
                os.getenv("REPORT_MINIMUM_COVERAGE_RATIO", "0.75")
            ),
            matrix_min_eligible_stations=int(
                os.getenv("REPORT_MATRIX_MIN_ELIGIBLE_STATIONS", "3")
            ),
        )
    except (TypeError, ValueError) as exc:
        raise ServiceError(
            "report_policy_invalid",
            "Environmental report policy configuration is invalid.",
            500,
        ) from exc
