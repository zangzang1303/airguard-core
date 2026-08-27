from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = (REPO_ROOT / "backend" / "db" / "schema.sql").read_text(encoding="utf-8")
MIGRATION_SQL = (
    REPO_ROOT / "backend" / "db" / "migrations" / "20260820_001_auth_foundation.sql"
).read_text(encoding="utf-8")


def _normalized(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.lower()).strip()


def test_bootstrap_contains_authentication_storage() -> None:
    sql = _normalized(SCHEMA_SQL)

    assert "email_normalized varchar(200) generated always as" in sql
    assert "create unique index if not exists uq_users_email_normalized" in sql
    assert "create table if not exists user_sessions" in sql
    assert "create table if not exists email_verification_tokens" in sql
    assert "create table if not exists password_reset_tokens" in sql


def test_authentication_secrets_are_hash_only() -> None:
    sql = _normalized(SCHEMA_SQL)

    assert "session_token_hash char(64)" in sql
    assert sql.count("token_hash char(64)") >= 3
    assert " session_token char(" not in sql
    assert " reset_token char(" not in sql
    assert " verification_token char(" not in sql


def test_authentication_artifacts_follow_user_lifecycle() -> None:
    sql = _normalized(SCHEMA_SQL)

    for table in ("user_sessions", "email_verification_tokens", "password_reset_tokens"):
        table_sql = sql.split(f"create table if not exists {table}", maxsplit=1)[1].split(");", maxsplit=1)[0]
        assert "references users(user_id) on delete cascade" in table_sql
        assert "expires_at timestamptz not null" in table_sql


def test_existing_database_migration_is_transactional_and_idempotent() -> None:
    sql = _normalized(MIGRATION_SQL)

    assert sql.startswith("-- airguard ai authentication data foundation.")
    assert " begin; " in f" {sql} "
    assert sql.endswith("commit;")
    assert "add column if not exists" in sql
    assert sql.count("create table if not exists") == 3
    assert "create unique index if not exists uq_users_email_normalized" in sql
