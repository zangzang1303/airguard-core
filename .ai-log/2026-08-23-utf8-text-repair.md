# AI Work Log

## Date / agent / machine

2026-08-23 / Codex / local Windows workspace

## Goal

Ensure the UTF-8 Vietnamese station and alert repair migration is applied in normal Compose startup
and the existing local-database bootstrap path.

## Context read

`AGENTS.md`, `README.md`, `tasks/frontend.md`, `docker-compose.yml`,
`docs/environment-setup.md`, `scripts/init-demo-db.ps1`, and the migration/test supplied in the
working tree.

## Files changed

- `docker-compose.yml`
- `scripts/init-demo-db.ps1`
- `docs/environment-setup.md`
- `tests/test_backend/test_vietnamese_station_alerts.py`

## Decisions and rationale

Migration `20260823_003_fix_vietnamese_station_names_and_alerts.sql` is idempotent and repairs
data already stored in a persistent PostgreSQL volume. It must therefore run from `db-migrate`,
not only be present in the repository. The local bootstrap script runs it after schema and seed so
legacy alert titles/descriptions are also repaired; PostgreSQL now mounts the migrations directory
read-only so that command has a valid in-container path.

## Commands/tests run and results

- Source inspection confirmed Compose previously ran only migrations 001 and 002.
- Focused pytest could not start because `.venv\\Scripts\\python.exe` points to a missing Windows
  Store Python installation.
- Docker is not installed/available in this shell, so Compose and API verification were not run.
- User-provided `db-migrate` logs identified and reproduced the SQL parse error at migration 003
  line 55: unqualified `description` was ambiguous between `alerts` and `stations`. It was changed
  to `alerts.description`; the transaction rolls back cleanly before that correction is rerun.

## Contracts/risks changed

No API or MQTT contract changed. The migration updates existing demo station metadata and alert
copy only.

## Blockers/open questions

Run verification on a machine with Docker Desktop and a working Python environment.

## Next exact step

Run `docker compose up -d --build`, then call `/api/v1/stations` and
`/api/v1/alerts?status=active` to confirm no corrupted Vietnamese text remains.

## Handoff IDs (request/message/proposal/job)

None.
