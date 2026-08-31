from __future__ import annotations

from pathlib import Path

SCHEMA_SQL = (
    Path(__file__).resolve().parents[2] / "backend" / "db" / "schema.sql"
).read_text(encoding="utf-8")
MIGRATION_SQL = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "db"
    / "migrations"
    / "20260824_005_add_demo_station_devices.sql"
).read_text(encoding="utf-8")
BACKFILL_MIGRATION_SQL = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "db"
    / "migrations"
    / "20260831_012_backfill_missing_demo_station_filters.sql"
).read_text(encoding="utf-8")


def test_every_demo_station_has_a_backend_registered_filter() -> None:
    for station_id in ("S01", "S02", "S03", "S04", "S05"):
        assert f"'{station_id}', 'offline', TRUE" in SCHEMA_SQL


def test_existing_database_migration_adds_missing_demo_station_filters() -> None:
    assert "BEGIN;" in MIGRATION_SQL
    assert "FILTER-S01" in MIGRATION_SQL
    assert "FILTER-04" in MIGRATION_SQL
    assert "ON CONFLICT (device_id) DO NOTHING" in MIGRATION_SQL
    assert MIGRATION_SQL.rstrip().endswith("COMMIT;")


def test_backfill_migration_brings_legacy_volumes_to_five_filters() -> None:
    assert "BEGIN;" in BACKFILL_MIGRATION_SQL
    assert "FILTER-02" in BACKFILL_MIGRATION_SQL
    assert "'S02', 'offline', TRUE" in BACKFILL_MIGRATION_SQL
    assert "FILTER-05" in BACKFILL_MIGRATION_SQL
    assert "'S05', 'offline', TRUE" in BACKFILL_MIGRATION_SQL
    assert "ON CONFLICT (device_id) DO NOTHING" in BACKFILL_MIGRATION_SQL
    assert BACKFILL_MIGRATION_SQL.rstrip().endswith("COMMIT;")


def test_compose_and_local_bootstrap_apply_filter_backfill() -> None:
    root = Path(__file__).resolve().parents[2]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    bootstrap = (root / "scripts" / "init-demo-db.ps1").read_text(encoding="utf-8")
    migration_path = "/migrations/20260831_012_backfill_missing_demo_station_filters.sql"

    assert migration_path in compose
    assert migration_path in bootstrap
