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


def test_every_demo_station_has_a_backend_registered_filter() -> None:
    for station_id in ("S01", "S02", "S03", "S04", "S05"):
        assert f"'{station_id}', 'offline', TRUE" in SCHEMA_SQL


def test_existing_database_migration_adds_missing_demo_station_filters() -> None:
    assert "BEGIN;" in MIGRATION_SQL
    assert "FILTER-S01" in MIGRATION_SQL
    assert "FILTER-04" in MIGRATION_SQL
    assert "ON CONFLICT (device_id) DO NOTHING" in MIGRATION_SQL
    assert MIGRATION_SQL.rstrip().endswith("COMMIT;")
