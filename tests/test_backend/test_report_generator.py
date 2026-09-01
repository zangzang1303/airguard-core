from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

import pytest

from backend.app.services.database import ServiceError
from backend.app.services.report_generator_service import (
    ReportGeneratorService,
    ReportPeriod,
    aggregate_report_statistics,
    render_report_html,
    render_report_markdown,
    render_report_pdf,
    resolve_report_period,
)
from backend.app.services.report_narrative_service import (
    NarrativeResult,
    NarrativeServiceError,
)
from backend.app.services.report_repository import ReportSourceData
from backend.app.tasks import report_tasks

PERIOD_START = datetime(2026, 8, 17, tzinfo=UTC)
PERIOD_END = datetime(2026, 8, 18, tzinfo=UTC)


def _measurement(station_id: str, measured_at: str, pm25: float, co2: float, **overrides):
    result = {
        "station_id": station_id,
        "measured_at": datetime.fromisoformat(measured_at),
        "pm25": pm25,
        "co2": co2,
        "noise_db": 60.0,
        "temperature": 31.0,
        "source": "simulator",
        "quality_flag": "valid",
    }
    result.update(overrides)
    return result


def source_fixture() -> ReportSourceData:
    measurements = [
        _measurement("S01", "2026-08-17T11:50:00+00:00", 60, 1200),
        _measurement("S01", "2026-08-17T11:55:00+00:00", 62, 1100),
        _measurement("S01", "2026-08-17T12:35:00+00:00", 30, 800),
        _measurement("S01", "2026-08-17T12:40:00+00:00", 32, 820),
        _measurement("S02", "2026-08-17T10:00:00+00:00", 20, 600),
        _measurement("S02", "2026-08-17T18:00:00+00:00", 22, 650),
        _measurement(
            "S05",
            "2026-08-17T09:00:00+00:00",
            500,
            900,
            quality_flag="invalid",
            source="untrusted",
        ),
    ]
    alerts = [
        {
            "alert_id": "a-1",
            "station_id": "S01",
            "alert_type": "pm25_threshold",
            "severity": "warning",
            "observed_value": 60,
            "threshold_value": 50,
            "created_at": datetime(2026, 8, 17, 11, 45, tzinfo=UTC),
        },
        {
            "alert_id": "a-2",
            "station_id": "S01",
            "alert_type": "co2_threshold",
            "severity": "critical",
            "observed_value": 1200,
            "threshold_value": 1000,
            "created_at": datetime(2026, 8, 17, 11, 46, tzinfo=UTC),
        },
    ]
    approvals = [
        {
            "request_id": "p-1",
            "station_id": "S01",
            "proposed_action": "ventilation_boost",
            "duration_minutes": 30,
            "status": "approved",
            "created_at": datetime(2026, 8, 17, 11, 50, tzinfo=UTC),
            # These fields must never enter evidence sent to a narrator.
            "reviewed_by": "00000000-0000-0000-0000-000000000099",
            "manager_email": "manager@example.test",
        },
        {
            "request_id": "p-2",
            "station_id": "S02",
            "proposed_action": "notify_station_area_users",
            "status": "rejected",
            "created_at": datetime(2026, 8, 17, 13, 0, tzinfo=UTC),
        },
    ]
    command_intents = [
        {
            "command_intent_id": "c-1",
            "command_id": "cmd-1",
            "approval_request_id": "p-1",
            "device_id": "FAN-01",
            "station_id": "S01",
            "command": "ventilation_boost",
            "status": "published",
            "approval_duration_minutes": 30,
            "created_at": datetime(2026, 8, 17, 11, 59, tzinfo=UTC),
            "dispatched_at": datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        },
        {
            "command_intent_id": "c-2",
            "command_id": "cmd-2",
            "approval_request_id": "p-eco",
            "device_id": "FAN-01",
            "station_id": "S01",
            "command": "eco_mode",
            "status": "published",
            "created_at": datetime(2026, 8, 17, 12, 30, tzinfo=UTC),
            "dispatched_at": datetime(2026, 8, 17, 12, 30, tzinfo=UTC),
        },
        {
            "command_intent_id": "c-failed",
            "device_id": "FAN-02",
            "station_id": "S02",
            "command": "ventilation_boost",
            "status": "failed",
            "approval_duration_minutes": 45,
            "created_at": datetime(2026, 8, 17, 15, 0, tzinfo=UTC),
        },
        {
            "command_intent_id": "c-unacknowledged",
            "command_id": "cmd-unacknowledged",
            "device_id": "FAN-02",
            "station_id": "S02",
            "command": "ventilation_boost",
            "status": "published",
            "duration_minutes": 30,
            "created_at": datetime(2026, 8, 17, 16, 0, tzinfo=UTC),
            "dispatched_at": datetime(2026, 8, 17, 16, 0, tzinfo=UTC),
        },
    ]
    events = [
        {
            "command_id": "cmd-1",
            "device_id": "FAN-01",
            "status": "succeeded",
            "operating_mode": "running_boost",
            "observed_at": datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
            "is_simulated": True,
        },
        {
            "command_id": "cmd-2",
            "device_id": "FAN-01",
            "status": "succeeded",
            "operating_mode": "eco_mode",
            "observed_at": datetime(2026, 8, 17, 12, 30, tzinfo=UTC),
            "is_simulated": True,
        },
    ]
    return ReportSourceData(measurements, alerts, approvals, command_intents, events)


class FakeReportRepository:
    def __init__(self, source: ReportSourceData | None = None) -> None:
        self.source = source or source_fixture()
        self.records: dict[tuple[str, datetime, datetime, str], dict] = {}
        self.load_count = 0
        self.clock = datetime(2026, 8, 21, tzinfo=UTC)
        self.lease_seconds = 300
        self.attempt_count = 0
        self.fail_next_load = False

    def reserve_report(self, *, report_type, period_start, period_end, timezone_name, generated_by):
        key = (report_type, period_start, period_end, timezone_name)
        if key in self.records:
            record = self.records[key]
            lease_expires_at = record.get("lease_expires_at")
            reclaimable = record["status"] == "failed" or (
                record["status"] == "generating" and (lease_expires_at is None or lease_expires_at <= self.clock)
            )
            if not reclaimable:
                return deepcopy(record), False
        else:
            report_id = str(uuid5(NAMESPACE_URL, ":".join(map(str, key))))
            record = {
                "report_id": report_id,
                "report_type": report_type,
                "period_start": period_start,
                "period_end": period_end,
                "timezone": timezone_name,
                "created_at": period_end,
            }
            self.records[key] = record
        self.attempt_count += 1
        record.update(
            status="generating",
            statistics={},
            evidence_summary={},
            narrative=None,
            generation_mode="deterministic_grounded",
            model_source="backend_deterministic_report_v1",
            generated_by=generated_by or record.get("generated_by"),
            failure_code=None,
            completed_at=None,
            generation_attempt_id=str(uuid5(NAMESPACE_URL, f"{record['report_id']}:attempt:{self.attempt_count}")),
            lease_expires_at=self.clock + timedelta(seconds=self.lease_seconds),
        )
        return deepcopy(record), True

    def load_source_data(self, *, period_start, period_end):
        self.load_count += 1
        if self.fail_next_load:
            self.fail_next_load = False
            raise ServiceError("report_source_unavailable", "temporary source failure", 503)
        return deepcopy(self.source)

    def complete_report(self, *, report_id, generation_attempt_id, **changes):
        record = self._by_id(report_id)
        self._require_attempt(record, generation_attempt_id)
        record.update(
            changes,
            status="completed",
            completed_at=record["period_end"],
            generation_attempt_id=None,
            lease_expires_at=None,
        )
        return deepcopy(record)

    def fail_report(self, *, report_id, generation_attempt_id, failure_code):
        record = self._by_id(report_id)
        self._require_attempt(record, generation_attempt_id)
        record.update(
            status="failed",
            failure_code=failure_code,
            completed_at=record["period_end"],
            generation_attempt_id=None,
            lease_expires_at=None,
        )
        return deepcopy(record)

    def list_reports(self, *, report_type=None, limit=50, offset=0):
        values = list(self.records.values())
        if report_type:
            values = [row for row in values if row["report_type"] == report_type]
        return deepcopy(values[offset : offset + limit])

    def get_report(self, report_id):
        try:
            return deepcopy(self._by_id(report_id))
        except KeyError as exc:
            raise ServiceError("report_not_found", "The environmental report was not found.", 404) from exc

    def _by_id(self, report_id):
        for row in self.records.values():
            if row["report_id"] == report_id:
                return row
        raise KeyError(report_id)

    @staticmethod
    def _require_attempt(record, generation_attempt_id):
        if record.get("status") != "generating" or record.get("generation_attempt_id") != generation_attempt_id:
            raise ServiceError(
                "report_generation_lease_lost",
                "This report generation attempt no longer owns the report lease.",
                409,
            )


class FailingNarrator:
    def generate(self, evidence_summary):
        raise NarrativeServiceError("narrative_provider_timeout")


class CapturingNarrator:
    def __init__(self) -> None:
        self.evidence = None

    def generate(self, evidence_summary):
        self.evidence = deepcopy(evidence_summary)
        return NarrativeResult(
            "The aggregate trend appears lower. Ventilation has a favorable comparative outcome. "
            "The result remains simulated and non-causal.",
            "live_llm",
            "test-live-model",
        )


def test_exact_daily_aggregation_uses_backend_aqi_and_operational_lifecycle() -> None:
    period = ReportPeriod("daily", PERIOD_START, PERIOD_END, "UTC")

    result = aggregate_report_statistics(source_fixture(), period)

    measurements = result["measurements"]
    assert measurements == {
        "valid_sample_count": 6,
        "excluded_sample_count": 1,
        "station_count": 2,
        "overall_avg_aqi": 104.83,
        "overall_max_aqi": 154,
        "worst_station_id": "S01",
        "stations": [
            {
                "station_id": "S01",
                "sample_count": 4,
                "avg_aqi": 122.25,
                "max_aqi": 154,
                "avg_pm25": 46.0,
                "max_pm25": 62,
                "avg_co2": 980.0,
                "max_co2": 1200,
                "avg_noise_db": 60.0,
                "max_noise_db": 60,
                "avg_temperature": 31.0,
                "max_temperature": 31,
            },
            {
                "station_id": "S02",
                "sample_count": 2,
                "avg_aqi": 70.0,
                "max_aqi": 72,
                "avg_pm25": 21.0,
                "max_pm25": 22,
                "avg_co2": 625.0,
                "max_co2": 650,
                "avg_noise_db": 60.0,
                "max_noise_db": 60,
                "avg_temperature": 31.0,
                "max_temperature": 31,
            },
        ],
    }
    assert result["alerts"] == {
        "total_count": 2,
        "threshold_exceedance_count": 2,
        "by_type": {"co2_threshold": 1, "pm25_threshold": 1},
        "by_severity": {"critical": 1, "warning": 1},
    }
    assert result["proposals"] == {
        "total_count": 2,
        "by_status": {"approved": 1, "rejected": 1},
        "by_action": {"notify_station_area_users": 1, "ventilation_boost": 1},
    }
    ventilation = result["ventilation"]
    assert ventilation["activation_count"] == 1
    assert ventilation["total_duration_minutes"] == 30.0
    assert ventilation["commanded_duration_minutes"] == 30.0
    assert ventilation["duration_basis"] == "observed_end_ack_only"
    assert ventilation["by_action"] == {"ventilation_boost": 1}
    assert ventilation["effectiveness"] == {
        "evaluated_cycle_count": 1,
        "insufficient_cycle_count": 0,
        "mean_pm25_change": -30.0,
        "mean_pm25_change_percent": -49.18,
        "mean_co2_change": -340.0,
        "mean_co2_change_percent": -29.57,
        "outcome": "improved",
    }
    assert result["data_quality"]["source_labels"] == ["simulator"]


def test_commanded_duration_is_not_reported_as_observed_without_end_ack() -> None:
    source = source_fixture()
    source_without_end = ReportSourceData(
        measurements=source.measurements,
        alerts=source.alerts,
        approvals=source.approvals,
        command_intents=[intent for intent in source.command_intents if intent.get("command") != "eco_mode"],
        device_status_events=[
            event for event in source.device_status_events if event.get("operating_mode") != "eco_mode"
        ],
    )

    ventilation = aggregate_report_statistics(
        source_without_end,
        ReportPeriod("daily", PERIOD_START, PERIOD_END, "UTC"),
    )["ventilation"]

    assert ventilation["activation_count"] == 1
    assert ventilation["total_duration_minutes"] == 0.0
    assert ventilation["commanded_duration_minutes"] == 30.0
    assert ventilation["effectiveness"]["evaluated_cycle_count"] == 0
    assert ventilation["effectiveness"]["insufficient_cycle_count"] == 1
    assert ventilation["effectiveness"]["outcome"] == "insufficient_data"


def test_generation_is_idempotent_for_type_range_and_timezone() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository)

    first = service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")
    second = service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")

    assert first["report_id"] == second["report_id"]
    assert first["status"] == second["status"] == "completed"
    assert first["reused"] is False
    assert second["reused"] is True
    assert repository.load_count == 1
    assert "generation_attempt_id" not in first
    assert "lease_expires_at" not in first


def test_fresh_generation_lease_signals_retry_instead_of_false_reuse() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository)
    repository.reserve_report(
        report_type="daily",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        timezone_name="UTC",
        generated_by=None,
    )

    with pytest.raises(ServiceError) as in_progress:
        service.generate_report(
            "daily",
            period_start=PERIOD_START,
            period_end=PERIOD_END,
            timezone_name="UTC",
            now=repository.clock,
        )

    assert in_progress.value.code == "report_generation_in_progress"
    assert in_progress.value.status_code == 503
    assert in_progress.value.details["retry_after_seconds"] >= repository.lease_seconds
    assert repository.load_count == 0


def test_failed_generation_is_immediately_reclaimed_by_retry() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository)
    repository.fail_next_load = True

    with pytest.raises(ServiceError) as first_attempt:
        service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")

    assert first_attempt.value.code == "report_source_unavailable"
    failed = next(iter(repository.records.values()))
    assert failed["status"] == "failed"
    assert failed["generation_attempt_id"] is None

    retried = service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")

    assert retried["status"] == "completed"
    assert retried["reused"] is False
    assert repository.attempt_count == 2
    assert repository.load_count == 2


def test_expired_generation_lease_is_reclaimed() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository)
    first, acquired = repository.reserve_report(
        report_type="daily",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        timezone_name="UTC",
        generated_by=None,
    )
    assert acquired is True
    repository.clock = first["lease_expires_at"] + timedelta(seconds=1)

    report = service.generate_report(
        "daily",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        timezone_name="UTC",
        now=repository.clock,
    )

    assert report["status"] == "completed"
    assert report["reused"] is False
    assert repository.attempt_count == 2


def test_reclaimed_report_rejects_late_write_from_stale_attempt() -> None:
    repository = FakeReportRepository()
    first, _ = repository.reserve_report(
        report_type="daily",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        timezone_name="UTC",
        generated_by=None,
    )
    repository.clock = first["lease_expires_at"] + timedelta(seconds=1)
    second, acquired = repository.reserve_report(
        report_type="daily",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        timezone_name="UTC",
        generated_by=None,
    )
    assert acquired is True

    with pytest.raises(ServiceError) as stale_write:
        repository.complete_report(
            report_id=first["report_id"],
            generation_attempt_id=first["generation_attempt_id"],
            statistics={},
        )

    assert stale_write.value.code == "report_generation_lease_lost"
    current = repository._by_id(second["report_id"])
    assert current["generation_attempt_id"] == second["generation_attempt_id"]
    assert current["status"] == "generating"


def test_report_task_waits_for_active_lease_before_retry(monkeypatch) -> None:
    class InProgressService:
        def generate_report(self, *args, **kwargs):
            raise ServiceError(
                "report_generation_in_progress",
                "active lease",
                503,
                {"retry_after_seconds": 287},
            )

    class RetryScheduledError(Exception):
        pass

    retry_call = {}

    def retry(*, exc, countdown):
        retry_call.update(exc=exc, countdown=countdown)
        raise RetryScheduledError

    monkeypatch.setattr(
        report_tasks,
        "build_report_service_from_environment",
        lambda: InProgressService(),
    )
    monkeypatch.setattr(report_tasks.generate_environmental_report_job, "retry", retry)

    with pytest.raises(RetryScheduledError):
        report_tasks.generate_environmental_report_job.run("daily")

    assert retry_call["countdown"] == 287
    assert str(retry_call["exc"]) == "report_generation_in_progress"


def test_llm_error_persists_complete_report_with_strict_grounded_fallback() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository, narrator=FailingNarrator())

    report = service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")

    assert report["status"] == "completed"
    assert report["generation_mode"] == "deterministic_grounded"
    assert report["model_source"] == "backend_deterministic_report_v1"
    assert report["failure_code"] == "narrative_provider_timeout"
    assert "6 mẫu hợp lệ" in report["narrative"] or "6 valid samples" in report["narrative"]
    assert "BÃ" not in report["narrative"]
    assert "â€”" not in report["narrative"]


def test_live_narrator_receives_aggregate_evidence_without_pii_or_secrets() -> None:
    repository = FakeReportRepository()
    narrator = CapturingNarrator()
    service = ReportGeneratorService(repository, narrator=narrator)

    report = service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")

    assert report["generation_mode"] == "live_llm"
    assert report["model_source"] == "test-live-model"
    serialized = repr(narrator.evidence).lower()
    assert "reviewed_by" not in serialized
    assert "manager_email" not in serialized
    assert "example.test" not in serialized
    assert "message_id" not in serialized


def test_default_periods_use_complete_local_calendar_boundaries() -> None:
    now = datetime(2026, 8, 21, 3, 0, tzinfo=UTC)  # 10:00 in Ho Chi Minh City.

    daily = resolve_report_period("daily", timezone_name="Asia/Ho_Chi_Minh", now=now)
    weekly = resolve_report_period("weekly", timezone_name="Asia/Ho_Chi_Minh", now=now)

    assert daily.period_start == datetime(2026, 8, 19, 17, 0, tzinfo=UTC)
    assert daily.period_end == datetime(2026, 8, 20, 17, 0, tzinfo=UTC)
    assert weekly.period_start == datetime(2026, 8, 9, 17, 0, tzinfo=UTC)
    assert weekly.period_end == datetime(2026, 8, 16, 17, 0, tzinfo=UTC)


def test_manual_period_requires_aware_pair_and_valid_timezone() -> None:
    with pytest.raises(ServiceError, match="timezone") as naive:
        resolve_report_period(
            "daily",
            period_start=datetime(2026, 8, 1),
            period_end=datetime(2026, 8, 2),
        )
    assert naive.value.code == "timezone_required"

    with pytest.raises(ServiceError) as incomplete:
        resolve_report_period("daily", period_start=PERIOD_START)
    assert incomplete.value.code == "invalid_report_period"

    with pytest.raises(ServiceError) as invalid_zone:
        resolve_report_period("daily", timezone_name="Not/A_Real_Zone")
    assert invalid_zone.value.code == "invalid_report_timezone"


def test_weekly_trend_compares_weekdays_and_weekend_in_report_timezone() -> None:
    period = ReportPeriod(
        "weekly",
        datetime(2026, 8, 17, tzinfo=UTC),
        datetime(2026, 8, 24, tzinfo=UTC),
        "UTC",
    )
    rows = [
        _measurement("S01", "2026-08-17T10:00:00+00:00", 12, 500),  # Monday, AQI 50
        _measurement("S01", "2026-08-18T10:00:00+00:00", 35.4, 500),  # Tuesday, AQI 100
        _measurement("S01", "2026-08-22T10:00:00+00:00", 55.4, 500),  # Saturday, AQI 150
        _measurement("S01", "2026-08-23T10:00:00+00:00", 35.4, 500),  # Sunday, AQI 100
    ]
    source = ReportSourceData(rows, [], [], [], [])

    trends = aggregate_report_statistics(source, period)["trends"]

    assert trends["weekday_avg_aqi"] == 75.0
    assert trends["weekend_avg_aqi"] == 125.0
    assert trends["weekend_minus_weekday_aqi"] == 50.0
    assert trends["direction"] == "worsening"


def test_markdown_and_html_export_render_only_the_same_stored_record() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository)
    generated = service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")
    stored = repository._by_id(generated["report_id"])
    stored["narrative"] = "Stored <script>alert('x')</script> narrative."

    markdown = service.export_report(generated["report_id"], "markdown")
    html_export = service.export_report(generated["report_id"], "html")

    assert markdown.media_type.startswith("text/markdown")
    assert "Stored <script>" in markdown.content.decode()
    rendered_html = html_export.content.decode()
    assert "Stored &lt;script&gt;" in rendered_html
    assert "<script>alert" not in rendered_html
    assert "S01" in rendered_html
    assert repository.load_count == 1


def test_pdf_export_is_lazy_and_structured_when_optional_dependency_is_missing() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository)
    generated = service.generate_report("daily", period_start=PERIOD_START, period_end=PERIOD_END, timezone_name="UTC")
    report = repository.get_report(generated["report_id"])

    try:
        content = render_report_pdf(report)
    except ServiceError as exc:
        assert exc.code == "pdf_export_dependency_missing"
        assert exc.status_code == 503
    else:
        assert content.startswith(b"%PDF")


def test_list_get_and_export_validation_return_structured_errors() -> None:
    repository = FakeReportRepository()
    service = ReportGeneratorService(repository)

    with pytest.raises(ServiceError) as bad_type:
        service.list_reports(report_type="monthly")
    assert bad_type.value.code == "invalid_report_type"

    with pytest.raises(ServiceError) as bad_id:
        service.get_report("not-a-uuid")
    assert bad_id.value.code == "invalid_report_id"

    generating, _ = repository.reserve_report(
        report_type="daily",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        timezone_name="UTC",
        generated_by=None,
    )
    with pytest.raises(ServiceError) as not_ready:
        service.export_report(generating["report_id"], "html")
    assert not_ready.value.code == "report_not_ready"


def test_render_helpers_reject_incomplete_stored_statistics() -> None:
    malformed = {"report_type": "daily", "statistics": {}, "narrative": "none"}
    with pytest.raises(ServiceError) as markdown_error:
        render_report_markdown(malformed)
    assert markdown_error.value.code == "report_record_invalid"
    with pytest.raises(ServiceError) as html_error:
        render_report_html(malformed)
    assert html_error.value.code == "report_record_invalid"
