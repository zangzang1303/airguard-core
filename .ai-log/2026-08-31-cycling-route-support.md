# AI Work Log

## Date / agent / machine

2026-08-31 / Codex / local Windows workspace

## Goal

Allow the Geospatial AI to answer Vietnamese cycling and walking route requests with grounded, activity-permitted routes.

## Context read

`AGENTS.md`, `specs/api-contracts.md`, geospatial agent, route, inhaled-dose services, and route tests.

## Files changed

- `backend/app/services/geospatial_agent_service.py`
- `backend/app/services/clean_running_route_service.py`
- `backend/app/services/inhaled_dose_service.py`
- `backend/app/main.py`
- `specs/api-contracts.md`
- `tests/test_backend/test_personalized_alerts_task2.py`
- `tests/test_backend/test_running_route_engine.py`

## Decisions and rationale

The agent now passes `activity=cycling|walking` to the canonical route service. The route service filters to bicycle- or foot-permitted graph edges, applies the activity snap gate, and records the activity in route provenance. Clearly labelled demo-only ventilation-rate policies support relative exposure ranking; they are not clinical estimates.

## Commands/tests run and results

- `git diff --check` passed.
- Python byte-compilation passed for the changed backend modules.
- Docker backend container is healthy.
- Attempted targeted pytest inside the backend container, but its production image does not include `pytest` (`No module named pytest`).

## Contracts/risks changed

The inhaled-mass API accepts `walking|cycling`; the clean-route API accepts `activity=walking|running|cycling`. Activity output remains simulator/demo-only and requires a policy review before any health-related production use.

## Next exact step

Rebuild/redeploy the backend, then run the targeted pytest suite in a test-capable image and issue the Vietnamese cycling prompt in the Geospatial AI drawer.
