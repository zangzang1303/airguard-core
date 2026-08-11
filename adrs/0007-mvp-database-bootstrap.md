# ADR 0007: Bootstrap schema and seed for the local MVP

## Status

Accepted for MVP/demo environments.

## Decision

Use `backend/db/schema.sql` and `backend/db/seed.sql` as the canonical local bootstrap
for PostgreSQL. Docker Compose applies them when the named volume is created, and
`scripts/init-demo-db.ps1` reapplies them safely for an existing local demo volume.

Do not introduce Alembic for the current MVP milestone. Any schema change must still
update the schema, seed, domain/API contracts and relevant tests in the same change.

## Scope and limitation

This decision applies only to the local/demo MVP. The bootstrap script is not a
replacement for versioned migrations in a shared, staging or production database.

## Consequences

The demo setup stays simple and reproducible, and the bootstrap is idempotent. A future
shared or production deployment must add a versioned migration process before accepting
non-rebuildable schema evolution.

## Verification

On 2026-08-11, `scripts/init-demo-db.ps1` ran twice successfully against the local
PostgreSQL volume; the database retained 5 stations, 3 seeded users and 1 simulated
device without duplicate seed rows.
