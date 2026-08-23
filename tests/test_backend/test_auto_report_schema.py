from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = (REPO_ROOT / "backend" / "db" / "schema.sql").read_text(encoding="utf-8")
SEED_SQL = (REPO_ROOT / "backend" / "db" / "seed.sql").read_text(encoding="utf-8")
MIGRATION_SQL = (REPO_ROOT / "backend" / "db" / "migrations" / "20260821_002_auto_ventilation_reports.sql").read_text(
    encoding="utf-8"
)


def test_auto_ventilation_lifecycle_schema_is_additive() -> None:
    for sql in (SCHEMA_SQL, MIGRATION_SQL):
        assert "duration_minutes" in sql
        assert "review_idempotency_key" in sql
        assert "command_id" in sql
        assert "acknowledged_at" in sql
        assert "CREATE TABLE IF NOT EXISTS device_status_events" in sql


def test_environmental_report_schema_has_idempotent_period_identity() -> None:
    for sql in (SCHEMA_SQL, MIGRATION_SQL):
        assert "CREATE TABLE IF NOT EXISTS environmental_reports" in sql
        assert "UNIQUE (report_type, period_start, period_end, timezone)" in sql
        assert "statistics JSONB" in sql
        assert "evidence_summary JSONB" in sql
        assert "generation_mode" in sql
        assert "generation_attempt_id UUID" in sql
        assert "lease_expires_at TIMESTAMPTZ" in sql
        assert "idx_environmental_reports_generation_lease" in sql


def test_reference_seed_matches_alert_schema_types() -> None:
    assert "'ALT-001'" not in SEED_SQL
    assert "threshold_value, unit, recommendation" not in SEED_SQL
    assert "00000000-0000-0000-0000-00000000a001" in SEED_SQL
