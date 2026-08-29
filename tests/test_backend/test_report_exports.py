from datetime import UTC, datetime
from io import BytesIO

from app.services.report_generator_service import (
    compute_content_checksum,
    render_report_html,
    render_report_markdown,
    render_report_pdf,
)
from pypdf import PdfReader


def report_fixture() -> dict:
    report = {
        "report_id": "11111111-1111-1111-1111-111111111111",
        "report_type": "daily",
        "period_start": datetime(2026, 8, 17, tzinfo=UTC),
        "period_end": datetime(2026, 8, 18, tzinfo=UTC),
        "timezone": "UTC",
        "schema_version": "b7-esg-reports-v1",
        "statistics": {
            "policy_snapshot": {"report_policy_version": "b7-esg-reports-v1"},
            "measurements": {"stations": [{"station_id": "S01", "sample_count": 10, "avg_aqi": 42, "max_aqi": 51, "avg_pm25": 12.5, "max_pm25": 18}], "valid_sample_count": 10, "excluded_sample_count": 0, "station_count": 1, "overall_avg_aqi": 42, "overall_max_aqi": 51, "worst_station_id": "S01"},
            "trends": {"direction": "stable", "daily_series": [], "weekday_avg_aqi": 42, "weekend_avg_aqi": None, "weekend_minus_weekday_aqi": None},
            "alerts": {"total_count": 0, "threshold_exceedance_count": 0, "by_type": {}, "by_severity": {}},
            "proposals": {"total_count": 0, "by_status": {}, "by_action": {}},
            "ventilation": {"activation_count": 0, "total_duration_minutes": 0, "by_action": {}, "effectiveness": {"outcome": "insufficient_data"}},
            "esg_metrics": {
                "estimated_pm25_removed_kg": {"value": None, "status": "insufficient_data", "reason_code": "no_acknowledged_boost_cycles", "formula_version": "estimated-device-impact-v1", "unit": "kg", "inputs": []},
                "estimated_energy_saved_kwh": {"value": None, "status": "insufficient_data", "reason_code": "no_acknowledged_eco_intervals", "formula_version": "estimated-device-impact-v1", "unit": "kWh", "inputs": []},
            },
            "reference_comparison": {"station_days": [], "annual_compliance_evaluated": False},
            "weekly_matrix": {"status": "not_applicable", "metric": "pm25", "unit": "ug/m3", "station_options": ["all_stations", "S01"], "views": [], "color_scale": {"version": "pm25-fixed-scale-v1", "clamp": True, "stops": [0, 15, 35, 45, 75, 150]}},
            "data_quality": {"source_labels": ["simulator"], "disclaimer": "Simulator-derived MVP data; not certified monitoring."},
        },
        "evidence_summary": {"allowed_claim_types": ["trend"]},
        "narrative": "The persisted qualitative pattern remains stable.",
        "generation_mode": "deterministic_grounded",
        "model_source": "backend_deterministic_report_v1",
        "failure_code": None,
        "created_at": datetime(2026, 8, 18, tzinfo=UTC),
        "completed_at": datetime(2026, 8, 18, tzinfo=UTC),
    }
    report["content_checksum_sha256"] = compute_content_checksum(report)
    return report


def test_canonical_checksum_is_stable_and_excludes_checksum_field() -> None:
    report = report_fixture()
    original = report["content_checksum_sha256"]
    report["content_checksum_sha256"] = "0" * 64
    assert compute_content_checksum(report) == original


def test_three_exports_share_persisted_report_id_checksum_and_fixture_values() -> None:
    report = report_fixture()
    markdown = render_report_markdown(report)
    html = render_report_html(report)
    pdf = render_report_pdf(report)
    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
    for output in (markdown, html):
        assert report["report_id"] in output
        assert report["content_checksum_sha256"] in output
        assert "12.5" in output
    assert "12.5" in pdf_text
    assert report["report_id"] not in pdf_text
    assert report["content_checksum_sha256"] not in pdf_text
    assert "Nhận định có căn cứ" in pdf_text
    assert "The persisted qualitative pattern" not in pdf_text
    assert pdf.startswith(b"%PDF-")


def test_legacy_report_exports_without_recalculation_or_fake_checksum() -> None:
    report = report_fixture()
    report.pop("schema_version")
    report.pop("content_checksum_sha256")
    report["statistics"].pop("esg_metrics")
    report["statistics"].pop("reference_comparison")
    report["statistics"].pop("weekly_matrix")
    markdown = render_report_markdown(report)
    assert "legacy-unavailable" in markdown
    assert "Chưa có đối chiếu tham chiếu" in markdown
