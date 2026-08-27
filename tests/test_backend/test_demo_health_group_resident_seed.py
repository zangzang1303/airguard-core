from pathlib import Path

MIGRATION_SQL = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "db"
    / "migrations"
    / "20260824_005_seed_demo_health_group_residents.sql"
).read_text(encoding="utf-8")


def test_demo_resident_seed_preserves_existing_user_ids() -> None:
    """Registered demo emails may already exist under non-canonical UUIDs."""
    assert "ON CONFLICT DO NOTHING" in MIGRATION_SQL
    assert "ON CONFLICT (user_id) DO UPDATE" not in MIGRATION_SQL
    assert "existing_user.email_normalized = canonical_users.email_normalized" in MIGRATION_SQL
    assert "SET\n    email = canonical_users.email" in MIGRATION_SQL


def test_demo_resident_seed_is_atomic_and_repairs_both_profiles() -> None:
    assert MIGRATION_SQL.count("BEGIN;") == 1
    assert MIGRATION_SQL.count("COMMIT;") == 1
    assert "sensitive.demo@airguard.local" in MIGRATION_SQL
    assert "outdoor.demo@airguard.local" in MIGRATION_SQL
    assert "'sensitive'" in MIGRATION_SQL
    assert "'outdoor_sport'" in MIGRATION_SQL
