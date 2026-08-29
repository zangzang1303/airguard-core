from pathlib import Path

import pytest
from app.main import ReportGenerateRequest, app
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]


def test_report_generate_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ReportGenerateRequest(type="daily", unexpected="not-allowed")


def test_openapi_report_schema_exposes_additive_integrity_fields() -> None:
    schema = app.openapi()["components"]["schemas"]["EnvironmentalReportResponse"]
    assert "schema_version" in schema["properties"]
    assert "content_checksum_sha256" in schema["properties"]


def test_report_routes_retain_manager_and_csrf_guards() -> None:
    source = (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    generate_block = source[source.index('@app.post("/api/v1/reports/generate"'):source.index('@app.get("/api/v1/reports/{report_id}"')]
    assert "Depends(require_manager)" in generate_block
    assert "validate_csrf(request)" in generate_block
    list_block = source[source.index('@app.get("/api/v1/reports"'):source.index('@app.post("/api/v1/reports/generate"')]
    assert "Depends(require_manager)" in list_block


def test_esg_migration_is_idempotent_and_backfills_legacy_schema() -> None:
    migration = (ROOT / "backend" / "db" / "migrations" / "20260829_007_esg_reports.sql").read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS schema_version" in migration
    assert "CREATE TABLE IF NOT EXISTS device_operating_profiles" in migration
    assert "ON CONFLICT (device_id, profile_version) DO UPDATE" in migration
    assert "periodic-report-v1" in migration
    assert "device_operating_profiles_no_overlap" in migration

