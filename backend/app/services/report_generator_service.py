from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from io import BytesIO
from statistics import fmean
from typing import Any, Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .air_quality import pm25_aqi
from .database import ServiceError
from .report_coverage_service import build_coverage_analytics
from .report_esg_service import calculate_esg_metrics
from .report_narrative_service import (
    NarrativeResult,
    NarrativeServiceError,
    ReportNarrator,
    validate_aggregate_evidence,
    validate_live_narrative,
    validate_model_source,
)
from .report_policy import REPORT_SCHEMA_VERSION, ReportPolicy
from .report_publication_service import (
    render_publication_html,
    render_publication_markdown,
    render_publication_pdf,
)
from .report_repository import ReportRepository, ReportSourceData

ReportType = Literal["daily", "weekly"]
ReportFormat = Literal["markdown", "html", "pdf"]
DEFAULT_REPORT_TIMEZONE = "Asia/Ho_Chi_Minh"
DETERMINISTIC_MODEL_SOURCE = "backend_deterministic_report_v1"
VENTILATION_ACTIONS = {"ventilation_boost", "air_purifier_on"}
ECO_ACTION = "eco_mode"
ACKNOWLEDGED_COMMAND_STATUSES = {
    "succeeded",
    "acknowledged",
    "completed",
    "running",
    "running_boost",
}


@dataclass(frozen=True)
class ReportPeriod:
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    timezone: str


@dataclass(frozen=True)
class ReportExport:
    content: bytes
    media_type: str
    filename: str


def resolve_report_period(
    report_type: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    timezone_name: str = DEFAULT_REPORT_TIMEZONE,
    now: datetime | None = None,
) -> ReportPeriod:
    normalized_type = _validate_report_type(report_type)
    timezone_name = str(timezone_name).strip()
    local_zone = _load_timezone(timezone_name)

    if (period_start is None) != (period_end is None):
        raise ServiceError(
            "invalid_report_period",
            "period_start and period_end must be provided together.",
            422,
        )
    if period_start is not None and period_end is not None:
        start = _require_aware(period_start, "period_start").astimezone(UTC)
        end = _require_aware(period_end, "period_end").astimezone(UTC)
        if end <= start:
            raise ServiceError("invalid_report_period", "period_end must be after period_start.", 422)
        return ReportPeriod(normalized_type, start, end, timezone_name)

    reference = now or datetime.now(UTC)
    reference = _require_aware(reference, "now").astimezone(local_zone)
    today = reference.date()
    if normalized_type == "daily":
        end_date = today
        start_date = today - timedelta(days=1)
    else:
        current_week_start = today - timedelta(days=today.weekday())
        end_date = current_week_start
        start_date = current_week_start - timedelta(days=7)
    local_start = datetime.combine(start_date, time.min, tzinfo=local_zone)
    local_end = datetime.combine(end_date, time.min, tzinfo=local_zone)
    return ReportPeriod(
        normalized_type,
        local_start.astimezone(UTC),
        local_end.astimezone(UTC),
        timezone_name,
    )


class ReportGeneratorService:
    def __init__(
        self,
        repository: ReportRepository,
        *,
        narrator: ReportNarrator | None = None,
        policy: ReportPolicy | None = None,
    ) -> None:
        self.repository = repository
        self.narrator = narrator
        self.policy = policy or ReportPolicy()

    def generate_report(
        self,
        report_type: str,
        *,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        timezone_name: str = DEFAULT_REPORT_TIMEZONE,
        generated_by: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        period = resolve_report_period(
            report_type,
            period_start=period_start,
            period_end=period_end,
            timezone_name=timezone_name,
            now=now,
        )
        actor_id = _validate_generated_by(generated_by)
        reserved, created = self.repository.reserve_report(
            report_type=period.report_type,
            period_start=period.period_start,
            period_end=period.period_end,
            timezone_name=period.timezone,
            generated_by=actor_id,
        )
        if not created:
            if reserved.get("status") == "completed":
                return {**_public_report_record(reserved), "reused": True}
            if reserved.get("status") == "generating":
                raise _report_generation_in_progress(reserved, now=now)
            raise ServiceError(
                "report_reservation_conflict",
                "The report could not be reclaimed for generation.",
                503,
                {"status": reserved.get("status")},
            )

        report_id = str(reserved["report_id"])
        generation_attempt_id = _generation_attempt_id(reserved)
        try:
            source_data = self.repository.load_source_data(
                period_start=period.period_start,
                period_end=period.period_end,
            )
            statistics = aggregate_report_statistics(source_data, period)
            active_station_ids = source_data.active_station_ids or sorted(
                {
                    str(row.get("station_id"))
                    for row in source_data.measurements
                    if row.get("station_id")
                }
            )
            coverage = build_coverage_analytics(
                source_data.measurements,
                period_start=period.period_start,
                period_end=period.period_end,
                timezone_name=period.timezone,
                report_type=period.report_type,
                active_station_ids=active_station_ids,
                policy=self.policy,
            )
            statistics["policy_snapshot"] = self.policy.snapshot()
            statistics["reference_comparison"] = coverage["reference_comparison"]
            statistics["weekly_matrix"] = coverage["weekly_matrix"]
            statistics["esg_metrics"] = calculate_esg_metrics(
                command_intents=source_data.command_intents,
                device_status_events=source_data.device_status_events,
                device_profiles=source_data.device_profiles,
                measurements=source_data.measurements,
                period_start=period.period_start,
                period_end=period.period_end,
                policy=self.policy,
            )
            statistics["data_quality"]["active_station_ids"] = coverage["active_station_ids"]
            statistics["data_quality"]["coverage_policy"] = {
                "expected_sample_interval_seconds": self.policy.expected_sample_interval_seconds,
                "minimum_coverage_ratio": self.policy.minimum_coverage_ratio,
            }
            evidence_summary = build_evidence_summary(statistics, period)
            narrative_result, narrative_failure = self._compose_narrative(evidence_summary, statistics)
            content_checksum = compute_content_checksum(
                {
                    **reserved,
                    "schema_version": REPORT_SCHEMA_VERSION,
                    "statistics": statistics,
                    "evidence_summary": evidence_summary,
                    "narrative": narrative_result.narrative,
                    "generation_mode": narrative_result.generation_mode,
                    "model_source": narrative_result.model_source,
                }
            )
            completed = self.repository.complete_report(
                report_id=report_id,
                generation_attempt_id=generation_attempt_id,
                statistics=statistics,
                evidence_summary=evidence_summary,
                narrative=narrative_result.narrative,
                generation_mode=narrative_result.generation_mode,
                model_source=narrative_result.model_source,
                failure_code=narrative_failure,
                schema_version=REPORT_SCHEMA_VERSION,
                content_checksum_sha256=content_checksum,
            )
            return {**_public_report_record(completed), "reused": False}
        except ServiceError as exc:
            self._persist_failure(report_id, generation_attempt_id, exc.code)
            raise
        except Exception as exc:
            self._persist_failure(report_id, generation_attempt_id, "report_generation_failed")
            raise ServiceError(
                "report_generation_failed",
                "The environmental report could not be generated.",
                500,
            ) from exc

    def list_reports(
        self,
        *,
        report_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        normalized_type = _validate_report_type(report_type) if report_type is not None else None
        if limit < 1 or limit > 200 or offset < 0:
            raise ServiceError("invalid_report_pagination", "Report pagination is invalid.", 422)
        return [
            _public_report_record(report)
            for report in self.repository.list_reports(
                report_type=normalized_type,
                limit=limit,
                offset=offset,
            )
        ]

    def get_report(self, report_id: str) -> dict[str, Any]:
        _validate_report_id(report_id)
        return _public_report_record(self.repository.get_report(report_id))

    def export_report(self, report_id: str, output_format: str) -> ReportExport:
        _validate_report_id(report_id)
        normalized_format = output_format.strip().lower()
        if normalized_format not in {"markdown", "html", "pdf"}:
            raise ServiceError(
                "unsupported_report_format",
                "Report format must be markdown, html, or pdf.",
                422,
            )
        report = self.repository.get_report(report_id)
        if report.get("status") != "completed":
            raise ServiceError(
                "report_not_ready",
                "Only a completed report can be exported.",
                409,
                {"status": report.get("status")},
            )
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "-", str(report["report_id"]))
        if normalized_format == "markdown":
            content = render_report_markdown(report).encode("utf-8")
            return ReportExport(content, "text/markdown; charset=utf-8", f"airguard-report-{safe_id}.md")
        if normalized_format == "html":
            content = render_report_html(report).encode("utf-8")
            return ReportExport(content, "text/html; charset=utf-8", f"airguard-report-{safe_id}.html")
        return ReportExport(
            render_report_pdf(report),
            "application/pdf",
            f"airguard-report-{safe_id}.pdf",
        )

    def _compose_narrative(
        self,
        evidence_summary: dict[str, Any],
        statistics: dict[str, Any],
    ) -> tuple[NarrativeResult, str | None]:
        fallback = NarrativeResult(
            narrative=deterministic_report_narrative(statistics),
            generation_mode="deterministic_grounded",
            model_source=DETERMINISTIC_MODEL_SOURCE,
        )
        if self.narrator is None:
            return fallback, "narrative_provider_not_configured"
        try:
            validate_aggregate_evidence(evidence_summary)
            result = self.narrator.generate(evidence_summary)
            if result.generation_mode != "live_llm":
                raise NarrativeServiceError("narrative_provider_not_live")
            narrative = validate_live_narrative(result.narrative)
            model_source = validate_model_source(result.model_source)
            return NarrativeResult(narrative, "live_llm", model_source), None
        except NarrativeServiceError as exc:
            return fallback, exc.code
        except Exception:
            return fallback, "narrative_provider_error"

    def _persist_failure(
        self,
        report_id: str,
        generation_attempt_id: str,
        failure_code: str,
    ) -> None:
        try:
            self.repository.fail_report(
                report_id=report_id,
                generation_attempt_id=generation_attempt_id,
                failure_code=_safe_failure_code(failure_code),
            )
        except Exception:
            # Preserve the original structured error; callers must not receive persistence internals.
            return


def aggregate_report_statistics(source: ReportSourceData, period: ReportPeriod) -> dict[str, Any]:
    zone = _load_timezone(period.timezone)
    valid_measurements: list[dict[str, Any]] = []
    excluded_measurements = 0
    for raw in source.measurements:
        measured_at = _coerce_aware(raw.get("measured_at"))
        pm25 = _finite_number(raw.get("pm25"))
        if (
            str(raw.get("quality_flag", "valid")).lower() != "valid"
            or measured_at is None
            or not (period.period_start <= measured_at < period.period_end)
            or pm25 is None
            or pm25 < 0
        ):
            excluded_measurements += 1
            continue
        valid_measurements.append(
            {
                "station_id": str(raw.get("station_id") or "unknown"),
                "measured_at": measured_at,
                "pm25": pm25,
                "aqi": pm25_aqi(pm25),
                "co2": _finite_number(raw.get("co2")),
                "noise_db": _finite_number(raw.get("noise_db")),
                "temperature": _finite_number(raw.get("temperature")),
                "source": str(raw.get("source") or "unknown"),
            }
        )

    stations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for measurement in valid_measurements:
        stations[measurement["station_id"]].append(measurement)
    station_rows = [_station_statistics(station_id, rows) for station_id, rows in sorted(stations.items())]
    all_aqi = [int(row["aqi"]) for row in valid_measurements if row.get("aqi") is not None]
    worst = max(
        station_rows,
        key=lambda row: (row["max_aqi"] if row["max_aqi"] is not None else -1, row["avg_aqi"] or -1, row["station_id"]),
        default=None,
    )
    measurements_statistics = {
        "valid_sample_count": len(valid_measurements),
        "excluded_sample_count": excluded_measurements,
        "station_count": len(station_rows),
        "overall_avg_aqi": _rounded_mean(all_aqi),
        "overall_max_aqi": max(all_aqi) if all_aqi else None,
        "worst_station_id": worst["station_id"] if worst else None,
        "stations": station_rows,
    }

    trend_statistics = _trend_statistics(valid_measurements, zone)
    alert_rows = _within_period(source.alerts, period, "created_at")
    approval_rows = _within_period(source.approvals, period, "created_at")
    alert_statistics = {
        "total_count": len(alert_rows),
        "threshold_exceedance_count": sum(
            1
            for row in alert_rows
            if (observed := _finite_number(row.get("observed_value"))) is not None
            and (threshold := _finite_number(row.get("threshold_value"))) is not None
            and observed > threshold
        ),
        "by_type": _counter_dict(row.get("alert_type") for row in alert_rows),
        "by_severity": _counter_dict(row.get("severity") for row in alert_rows),
    }
    proposal_statistics = {
        "total_count": len(approval_rows),
        "by_status": _counter_dict(row.get("status") for row in approval_rows),
        "by_action": _counter_dict(row.get("proposed_action") for row in approval_rows),
    }
    ventilation_statistics = _ventilation_statistics(
        source.command_intents,
        source.device_status_events,
        valid_measurements,
        period,
    )
    source_labels = sorted({row["source"] for row in valid_measurements if row.get("source")})
    return {
        "measurements": measurements_statistics,
        "trends": trend_statistics,
        "alerts": alert_statistics,
        "proposals": proposal_statistics,
        "ventilation": ventilation_statistics,
        "data_quality": {
            "source_labels": source_labels,
            "disclaimer": (
                "Simulator-derived MVP data; not certified monitoring and not evidence of medical, "
                "legal, or causal conclusions."
            ),
        },
    }


def build_evidence_summary(statistics: dict[str, Any], period: ReportPeriod) -> dict[str, Any]:
    evidence = {
        "report_type": period.report_type,
        "period": {
            "start": period.period_start.isoformat(),
            "end": period.period_end.isoformat(),
            "timezone": period.timezone,
        },
        "measurements": statistics["measurements"],
        "trends": statistics["trends"],
        "alerts": statistics["alerts"],
        "proposals": statistics["proposals"],
        "ventilation": statistics["ventilation"],
        "coverage": {
            "policy": statistics.get("policy_snapshot", {}),
            "active_station_ids": statistics.get("data_quality", {}).get("active_station_ids", []),
        },
        "reference_comparison": statistics.get("reference_comparison", {}),
        "acknowledged_activity": statistics.get("esg_metrics", {}).get("acknowledged_intervals", []),
        "esg_metrics": statistics.get("esg_metrics", {}),
        "data_quality": statistics["data_quality"],
        "allowed_claim_types": [
            "trend",
            "coverage",
            "reference",
            "acknowledged_activity",
            "estimate_availability",
        ],
    }
    validate_aggregate_evidence(evidence)
    return evidence


def deterministic_report_narrative(statistics: dict[str, Any]) -> str:
    measurements = statistics["measurements"]
    alerts = statistics["alerts"]
    ventilation = statistics["ventilation"]
    average_aqi = measurements.get("overall_avg_aqi")
    worst_station = measurements.get("worst_station_id")
    first = (
        f"Báo cáo ghi nhận {measurements['valid_sample_count']} mẫu hợp lệ từ "
        f"{measurements['station_count']} trạm mô phỏng."
    )
    if average_aqi is None:
        second = "Chưa đủ mẫu hợp lệ để tính AQI trung bình hoặc xác định trạm có giá trị cao nhất."
    else:
        second = f"AQI trung bình là {average_aqi:g}; giá trị AQI cao nhất trong kỳ được ghi nhận tại {worst_station}."
    third = (
        f"Backend ghi nhận {alerts['total_count']} vòng đời cảnh báo và "
        f"{ventilation['activation_count']} lượt thông gió đã được xác nhận; thời lượng quan sát là "
        f"{ventilation['total_duration_minutes']:g} phút và thời lượng được ra lệnh là "
        f"{ventilation['commanded_duration_minutes']:g} phút."
    )
    outcome = ventilation["effectiveness"]["outcome"]
    fourth = (
        f"Kết quả so sánh trước và sau là {outcome}; thông tin này không dùng để kết luận "
        "quan hệ nguyên nhân-kết quả."
    )
    return " ".join((first, second, third, fourth))


def render_report_markdown(report: dict[str, Any]) -> str:
    return render_publication_markdown(report)


def _legacy_render_report_markdown(report: dict[str, Any]) -> str:
    statistics = _stored_statistics(report)
    measurements = statistics["measurements"]
    lines = [
        f"# AirGuard environmental report - {report['report_type']}",
        "",
        f"- Period: {_iso(report.get('period_start'))} to {_iso(report.get('period_end'))}",
        f"- Timezone: {report.get('timezone')}",
        f"- Generation mode: {report.get('generation_mode')}",
        "",
        "## Summary",
        "",
        str(report.get("narrative") or "No narrative is available."),
        "",
        "## Station statistics",
        "",
        "| Station | Samples | Avg AQI | Max AQI | Avg PM2.5 | Max PM2.5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in measurements.get("stations", []):
        lines.append(
            f"| {row['station_id']} | {row['sample_count']} | {_display(row['avg_aqi'])} | "
            f"{_display(row['max_aqi'])} | {_display(row['avg_pm25'])} | {_display(row['max_pm25'])} |"
        )
    lines.extend(
        [
            "",
            "## Operational summary",
            "",
            f"- Alerts: {statistics['alerts']['total_count']}",
            f"- Threshold exceedances: {statistics['alerts']['threshold_exceedance_count']}",
            f"- Proposals: {statistics['proposals']['total_count']}",
            f"- Ventilation activations: {statistics['ventilation']['activation_count']}",
            f"- Observed ventilation duration: {statistics['ventilation']['total_duration_minutes']} minutes",
            f"- Commanded ventilation duration: {statistics['ventilation']['commanded_duration_minutes']} minutes",
            "",
            f"> {statistics['data_quality']['disclaimer']}",
            "",
        ]
    )
    return "\n".join(lines)


def render_report_html(report: dict[str, Any]) -> str:
    return render_publication_html(report)


def _legacy_render_report_html(report: dict[str, Any]) -> str:
    statistics = _stored_statistics(report)
    station_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row['station_id']))}</td>"
        f"<td>{row['sample_count']}</td>"
        f"<td>{html.escape(_display(row['avg_aqi']))}</td>"
        f"<td>{html.escape(_display(row['max_aqi']))}</td>"
        f"<td>{html.escape(_display(row['avg_pm25']))}</td>"
        f"<td>{html.escape(_display(row['max_pm25']))}</td>"
        "</tr>"
        for row in statistics["measurements"].get("stations", [])
    )
    narrative = html.escape(str(report.get("narrative") or "No narrative is available."))
    disclaimer = html.escape(str(statistics["data_quality"]["disclaimer"]))
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        "<title>AirGuard environmental report</title>"
        "<style>body{font-family:Arial,sans-serif;color:#172033;margin:2rem}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccd3dd;padding:.5rem;text-align:left}"
        ".disclaimer{margin-top:2rem;color:#52606d;font-size:.9rem}</style></head><body>"
        f"<h1>AirGuard environmental report - {html.escape(str(report['report_type']))}</h1>"
        f"<p><strong>Period:</strong> {html.escape(_iso(report.get('period_start')))} - "
        f"{html.escape(_iso(report.get('period_end')))} ({html.escape(str(report.get('timezone')))})</p>"
        f"<p><strong>Generation mode:</strong> {html.escape(str(report.get('generation_mode')))}</p>"
        f"<h2>Summary</h2><p>{narrative}</p>"
        "<h2>Station statistics</h2><table><thead><tr><th>Station</th><th>Samples</th>"
        "<th>Avg AQI</th><th>Max AQI</th><th>Avg PM2.5</th><th>Max PM2.5</th></tr></thead>"
        f"<tbody>{station_rows}</tbody></table>"
        f'<p class="disclaimer">{disclaimer}</p></body></html>'
    )


def render_report_pdf(report: dict[str, Any]) -> bytes:
    return render_publication_pdf(report)


def _legacy_render_report_pdf(report: dict[str, Any]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise ServiceError(
            "pdf_export_dependency_missing",
            "PDF export is unavailable because the optional reportlab dependency is not installed.",
            503,
        ) from exc

    statistics = _stored_statistics(report)
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, title="AirGuard environmental report")
    styles = getSampleStyleSheet()
    story: list[Any] = [
        Paragraph(f"AirGuard environmental report - {html.escape(str(report['report_type']))}", styles["Title"]),
        Spacer(1, 12),
        Paragraph(html.escape(str(report.get("narrative") or "No narrative is available.")), styles["BodyText"]),
        Spacer(1, 12),
    ]
    table_data = [["Station", "Samples", "Avg AQI", "Max AQI", "Avg PM2.5", "Max PM2.5"]]
    for row in statistics["measurements"].get("stations", []):
        table_data.append(
            [
                str(row["station_id"]),
                str(row["sample_count"]),
                _display(row["avg_aqi"]),
                _display(row["max_aqi"]),
                _display(row["avg_pm25"]),
                _display(row["max_pm25"]),
            ]
        )
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF6")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9AA7B7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(
        [
            table,
            Spacer(1, 12),
            Paragraph(html.escape(str(statistics["data_quality"]["disclaimer"])), styles["BodyText"]),
        ]
    )
    document.build(story)
    return buffer.getvalue()


def _station_statistics(station_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "station_id": station_id,
        "sample_count": len(rows),
        "avg_aqi": _rounded_mean(row.get("aqi") for row in rows),
        "max_aqi": _maximum(row.get("aqi") for row in rows),
        "avg_pm25": _rounded_mean(row.get("pm25") for row in rows),
        "max_pm25": _maximum(row.get("pm25") for row in rows),
        "avg_co2": _rounded_mean(row.get("co2") for row in rows),
        "max_co2": _maximum(row.get("co2") for row in rows),
        "avg_noise_db": _rounded_mean(row.get("noise_db") for row in rows),
        "max_noise_db": _maximum(row.get("noise_db") for row in rows),
        "avg_temperature": _rounded_mean(row.get("temperature") for row in rows),
        "max_temperature": _maximum(row.get("temperature") for row in rows),
    }


def _trend_statistics(rows: list[dict[str, Any]], zone: ZoneInfo) -> dict[str, Any]:
    grouped: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["measured_at"].astimezone(zone).date()].append(row)
    daily_series: list[dict[str, Any]] = []
    for day, items in sorted(grouped.items()):
        daily_series.append(
            {
                "date": day.isoformat(),
                "valid_sample_count": len(items),
                "avg_aqi": _rounded_mean(item.get("aqi") for item in items),
                "avg_pm25": _rounded_mean(item.get("pm25") for item in items),
            }
        )
    daily_values = [row["avg_aqi"] for row in daily_series if row["avg_aqi"] is not None]
    if len(daily_values) < 2:
        direction = "insufficient_data"
    elif daily_values[-1] < daily_values[0]:
        direction = "improving"
    elif daily_values[-1] > daily_values[0]:
        direction = "worsening"
    else:
        direction = "stable"
    weekdays = [row["avg_aqi"] for row in daily_series if date.fromisoformat(row["date"]).weekday() < 5]
    weekends = [row["avg_aqi"] for row in daily_series if date.fromisoformat(row["date"]).weekday() >= 5]
    weekday_average = _rounded_mean(weekdays)
    weekend_average = _rounded_mean(weekends)
    difference = (
        round(weekend_average - weekday_average, 2)
        if weekday_average is not None and weekend_average is not None
        else None
    )
    return {
        "direction": direction,
        "daily_series": daily_series,
        "weekday_avg_aqi": weekday_average,
        "weekend_avg_aqi": weekend_average,
        "weekend_minus_weekday_aqi": difference,
    }


def _ventilation_statistics(
    command_intents: list[dict[str, Any]],
    status_events: list[dict[str, Any]],
    measurements: list[dict[str, Any]],
    period: ReportPeriod,
) -> dict[str, Any]:
    events_by_command: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eco_events_by_device: dict[str, list[datetime]] = defaultdict(list)
    for event in status_events:
        observed_at = _coerce_aware(event.get("observed_at") or event.get("timestamp") or event.get("created_at"))
        if observed_at is None:
            continue
        command_id = event.get("command_id")
        if command_id:
            events_by_command[str(command_id)].append({**event, "_time": observed_at})
        mode = str(
            event.get("device_state") or event.get("operating_mode") or event.get("action") or event.get("status") or ""
        ).lower()
        if mode == ECO_ACTION and event.get("device_id"):
            eco_events_by_device[str(event["device_id"])].append(observed_at)
    for values in eco_events_by_device.values():
        values.sort()

    eco_intents_by_device: dict[str, list[datetime]] = defaultdict(list)
    for intent in command_intents:
        action = _intent_action(intent)
        if action != ECO_ACTION or not _intent_was_acknowledged(intent, events_by_command):
            continue
        started_at = _intent_start(intent, events_by_command)
        if started_at is not None and intent.get("device_id"):
            eco_intents_by_device[str(intent["device_id"])].append(started_at)
    for values in eco_intents_by_device.values():
        values.sort()

    cycles: list[dict[str, Any]] = []
    by_action: Counter[str] = Counter()
    for intent in sorted(
        command_intents, key=lambda row: _intent_start(row, events_by_command) or datetime.max.replace(tzinfo=UTC)
    ):
        action = _intent_action(intent)
        if action not in VENTILATION_ACTIONS or not _intent_was_acknowledged(intent, events_by_command):
            continue
        started_at = _intent_start(intent, events_by_command)
        if started_at is None:
            continue
        device_id = str(intent.get("device_id") or "unknown")
        station_id = str(intent.get("station_id") or "unknown")
        explicit_end = _coerce_aware(intent.get("completed_at"))
        end_candidates = [
            value
            for value in [*eco_events_by_device.get(device_id, []), *eco_intents_by_device.get(device_id, [])]
            if value > started_at
        ]
        observed_end = explicit_end or (min(end_candidates) if end_candidates else None)
        if observed_end is not None and observed_end <= started_at:
            observed_end = None
        commanded_duration = _intent_duration(intent)
        commanded_end = started_at + timedelta(minutes=commanded_duration) if commanded_duration is not None else None
        observed_minutes = _period_overlap_minutes(
            started_at,
            observed_end,
            period,
        )
        commanded_minutes = _period_overlap_minutes(
            started_at,
            commanded_end,
            period,
        )
        if (
            observed_minutes <= 0
            and commanded_minutes <= 0
            and not (period.period_start <= started_at < period.period_end)
        ):
            continue
        cycles.append(
            {
                "station_id": station_id,
                "device_id": device_id,
                "action": action,
                "started_at": started_at,
                "ended_at": observed_end,
                "observed_duration_minutes": observed_minutes,
                "commanded_duration_minutes": commanded_minutes,
            }
        )
        by_action[action] += 1

    effectiveness = _ventilation_effectiveness(cycles, measurements)
    return {
        "activation_count": len(cycles),
        "total_duration_minutes": round(sum(cycle["observed_duration_minutes"] for cycle in cycles), 2),
        "commanded_duration_minutes": round(sum(cycle["commanded_duration_minutes"] for cycle in cycles), 2),
        "duration_basis": "observed_end_ack_only",
        "by_action": dict(sorted(by_action.items())),
        "effectiveness": effectiveness,
    }


def _period_overlap_minutes(
    started_at: datetime,
    ended_at: datetime | None,
    period: ReportPeriod,
) -> float:
    if ended_at is None or ended_at <= started_at:
        return 0.0
    overlap_start = max(started_at, period.period_start)
    overlap_end = min(ended_at, period.period_end)
    if overlap_end <= overlap_start:
        return 0.0
    return (overlap_end - overlap_start).total_seconds() / 60


def _ventilation_effectiveness(cycles: list[dict[str, Any]], measurements: list[dict[str, Any]]) -> dict[str, Any]:
    pm25_changes: list[float] = []
    pm25_percent_changes: list[float] = []
    co2_changes: list[float] = []
    co2_percent_changes: list[float] = []
    insufficient = 0
    for cycle in cycles:
        ended_at = cycle.get("ended_at")
        if ended_at is None:
            insufficient += 1
            continue
        station_rows = [row for row in measurements if row["station_id"] == cycle["station_id"]]
        before = [
            row
            for row in station_rows
            if cycle["started_at"] - timedelta(minutes=15) <= row["measured_at"] < cycle["started_at"]
        ]
        after = [row for row in station_rows if ended_at <= row["measured_at"] < ended_at + timedelta(minutes=15)]
        before_pm25 = _rounded_mean(row.get("pm25") for row in before)
        after_pm25 = _rounded_mean(row.get("pm25") for row in after)
        before_co2 = _rounded_mean(row.get("co2") for row in before)
        after_co2 = _rounded_mean(row.get("co2") for row in after)
        evaluated = False
        if before_pm25 is not None and after_pm25 is not None:
            change = after_pm25 - before_pm25
            pm25_changes.append(change)
            if before_pm25 > 0:
                pm25_percent_changes.append(change / before_pm25 * 100)
            evaluated = True
        if before_co2 is not None and after_co2 is not None:
            change = after_co2 - before_co2
            co2_changes.append(change)
            if before_co2 > 0:
                co2_percent_changes.append(change / before_co2 * 100)
            evaluated = True
        if not evaluated:
            insufficient += 1

    evaluated_count = len(cycles) - insufficient
    mean_pm25_change = _rounded_mean(pm25_changes)
    mean_co2_change = _rounded_mean(co2_changes)
    known_changes = [value for value in (mean_pm25_change, mean_co2_change) if value is not None]
    if not known_changes:
        outcome = "insufficient_data"
    elif all(value < 0 for value in known_changes):
        outcome = "improved"
    elif all(value > 0 for value in known_changes):
        outcome = "worsened"
    else:
        outcome = "mixed"
    return {
        "evaluated_cycle_count": evaluated_count,
        "insufficient_cycle_count": insufficient,
        "mean_pm25_change": mean_pm25_change,
        "mean_pm25_change_percent": _rounded_mean(pm25_percent_changes),
        "mean_co2_change": mean_co2_change,
        "mean_co2_change_percent": _rounded_mean(co2_percent_changes),
        "outcome": outcome,
    }


def _intent_action(intent: dict[str, Any]) -> str:
    return str(intent.get("command") or intent.get("action") or intent.get("approval_action") or "").lower()


def _intent_was_acknowledged(intent: dict[str, Any], events_by_command: dict[str, list[dict[str, Any]]]) -> bool:
    if str(intent.get("status") or "").lower() in ACKNOWLEDGED_COMMAND_STATUSES:
        return True
    if str(intent.get("ack_status") or "").lower() in ACKNOWLEDGED_COMMAND_STATUSES:
        return True
    command_id = intent.get("command_id")
    return bool(
        command_id
        and any(
            str(event.get("status") or "").lower() in ACKNOWLEDGED_COMMAND_STATUSES
            for event in events_by_command.get(str(command_id), [])
        )
    )


def _intent_start(intent: dict[str, Any], events_by_command: dict[str, list[dict[str, Any]]]) -> datetime | None:
    explicit = _coerce_aware(intent.get("acknowledged_at") or intent.get("dispatched_at") or intent.get("created_at"))
    command_id = intent.get("command_id")
    if command_id:
        successful_events = [
            event["_time"]
            for event in events_by_command.get(str(command_id), [])
            if str(event.get("status") or "").lower() in ACKNOWLEDGED_COMMAND_STATUSES
            or str(event.get("operating_mode") or "").lower() in {"running_boost", "air_purifier_on"}
        ]
        if successful_events:
            return min(successful_events)
    return explicit


def _intent_duration(intent: dict[str, Any]) -> float | None:
    for key in ("duration_minutes", "approval_duration_minutes"):
        value = _finite_number(intent.get(key))
        if value is not None and value > 0:
            return value
    for container_key in ("action_parameters", "evidence"):
        container = intent.get(container_key)
        if isinstance(container, dict):
            value = _finite_number(container.get("duration_minutes"))
            if value is not None and value > 0:
                return value
    return None


def _within_period(rows: Iterable[dict[str, Any]], period: ReportPeriod, timestamp_key: str) -> list[dict[str, Any]]:
    accepted = []
    for row in rows:
        timestamp = _coerce_aware(row.get(timestamp_key))
        if timestamp is not None and period.period_start <= timestamp < period.period_end:
            accepted.append(row)
    return accepted


def canonical_content_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_id": str(report.get("report_id")),
        "report_type": str(report.get("report_type")),
        "period_start": _iso(report.get("period_start")),
        "period_end": _iso(report.get("period_end")),
        "timezone": str(report.get("timezone")),
        "schema_version": str(report.get("schema_version") or REPORT_SCHEMA_VERSION),
        "statistics": report.get("statistics"),
        "evidence_summary": report.get("evidence_summary"),
        "narrative": str(report.get("narrative") or ""),
        "generation_mode": str(report.get("generation_mode") or ""),
        "model_source": str(report.get("model_source") or ""),
    }


def compute_content_checksum(report: dict[str, Any]) -> str:
    payload = canonical_content_payload(report)
    try:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ServiceError(
            "report_record_invalid",
            "Report content cannot be serialized canonically.",
            500,
        ) from exc
    return hashlib.sha256(canonical).hexdigest()


def _stored_statistics(report: dict[str, Any]) -> dict[str, Any]:
    statistics = report.get("statistics")
    if not isinstance(statistics, dict):
        raise ServiceError("report_record_invalid", "Stored report statistics are invalid.", 500)
    required = {"measurements", "trends", "alerts", "proposals", "ventilation", "data_quality"}
    if not required.issubset(statistics):
        raise ServiceError("report_record_invalid", "Stored report statistics are incomplete.", 500)
    return statistics


def _validate_report_type(report_type: str) -> ReportType:
    normalized = str(report_type).strip().lower()
    if normalized not in {"daily", "weekly"}:
        raise ServiceError("invalid_report_type", "Report type must be daily or weekly.", 422)
    return normalized  # type: ignore[return-value]


def _validate_generated_by(generated_by: str | None) -> str | None:
    if generated_by is None:
        return None
    try:
        return str(UUID(generated_by))
    except (ValueError, TypeError) as exc:
        raise ServiceError("invalid_generated_by", "generated_by must be a UUID.", 422) from exc


def _validate_report_id(report_id: str) -> str:
    try:
        return str(UUID(report_id))
    except (ValueError, TypeError) as exc:
        raise ServiceError("invalid_report_id", "Report ID must be a UUID.", 422) from exc


def _generation_attempt_id(report: dict[str, Any]) -> str:
    try:
        return str(UUID(str(report.get("generation_attempt_id"))))
    except (ValueError, TypeError) as exc:
        raise ServiceError(
            "report_reservation_invalid",
            "The report generation reservation is missing its attempt identifier.",
            500,
        ) from exc


def _report_generation_in_progress(report: dict[str, Any], *, now: datetime | None) -> ServiceError:
    lease_expires_at = _coerce_aware(report.get("lease_expires_at"))
    reference = _coerce_aware(now) or datetime.now(UTC)
    retry_after_seconds = 1
    if lease_expires_at is not None:
        retry_after_seconds = max(
            1,
            int((lease_expires_at - reference).total_seconds()) + 1,
        )
    return ServiceError(
        "report_generation_in_progress",
        "Another worker currently owns the report generation lease.",
        503,
        {"status": "generating", "retry_after_seconds": retry_after_seconds},
    )


def _public_report_record(report: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in report.items() if key not in {"generation_attempt_id", "lease_expires_at"}}


def _load_timezone(timezone_name: str):
    """Load an IANA zone while keeping common MVP zones usable on bare Windows Python."""
    if timezone_name in {"UTC", "Etc/UTC", "GMT"}:
        return UTC
    if timezone_name == DEFAULT_REPORT_TIMEZONE:
        # Vietnam has observed UTC+07:00 continuously since 1975. This fallback keeps
        # report workers deterministic when the optional OS/tzdata database is absent.
        return timezone(timedelta(hours=7), name=DEFAULT_REPORT_TIMEZONE)
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ServiceError("invalid_report_timezone", "The report timezone is invalid.", 422) from exc


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ServiceError("timezone_required", f"{field_name} must include a timezone.", 422)
    return value


def _coerce_aware(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        candidate = value
    elif isinstance(value, str):
        try:
            candidate = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if candidate.tzinfo is None or candidate.tzinfo.utcoffset(candidate) is None:
        return None
    return candidate.astimezone(UTC)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _rounded_mean(values: Iterable[Any]) -> float | None:
    numbers = [number for value in values if (number := _finite_number(value)) is not None]
    return round(fmean(numbers), 2) if numbers else None


def _maximum(values: Iterable[Any]) -> float | int | None:
    numbers = [number for value in values if (number := _finite_number(value)) is not None]
    if not numbers:
        return None
    maximum = max(numbers)
    return int(maximum) if maximum.is_integer() else round(maximum, 2)


def _counter_dict(values: Iterable[Any]) -> dict[str, int]:
    counter = Counter(str(value) for value in values if value is not None and str(value).strip())
    return dict(sorted(counter.items()))


def _safe_failure_code(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_.-]", "_", str(value).lower())[:100]
    return normalized or "report_generation_failed"


def _display(value: Any) -> str:
    return "N/A" if value is None else str(value)


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")
