# AI Work Log

## Date / agent / machine

2026-08-29 / Codex / Windows workspace `D:\Ai_Thuc_Chien\P-074`.

## Goal

Implement B7-02.0 through B7-02.7 for contract `b7-personalized-alerts-v1`: grounded inhaled-mass
estimation, deterministic clean-running route, predictive-warning email, independent consent,
authenticated checklist, Agent/frontend integration and evidence.

## Context read

`AGENTS.md`, `README.md`, Task 2, API/domain specs, referenced backend/Agent tasks, test plan,
definition of done, ADR 0003/0004/0006/0009/0014 and current service/test ownership.

## Files changed

Backend settings/API/services/repositories/tasks, schema and migration 006; graph snapshot/exporter;
frontend API/types/profile/alerts/map/Agent drawer and scripts; API/domain specs; ADR 0019; README,
demo/test runbooks and Task 2 status. See `git status --short` for the exact list.

Existing user/other-agent changes in `tasks/backlog7/README.md`,
`tasks/backlog7/task5-periodic-reports-ai-narrative.md`, and `.claude/settings.local.json` were not
reverted or edited as part of Task 2.

## Decisions and rationale

- Backend remains the only source of environmental facts; all quality-gate failures fail closed.
- Exposure output is `estimated_inhaled_mass_ug` using Decimal and versioned ventilation presets.
- Runtime graph source remains `curated_demo_graph`; no request-path OSM call.
- `/agent/chat` delegates to the same `CleanRunningRouteService`; unavailable service returns a
  deterministic insufficient-data response without geometry or numbers.
- Predictive episode preserves its original forecast target when rolling forecasts move later,
  allowing a two-hour candidate to enter the 30–60 minute delivery window. Earlier targets and
  warning→critical escalation still update evidence.
- Consent is two independent backend-owned booleans defaulting false. Deep links contain only
  panel, allow-listed station and episode UUID.

## Commands/tests run and results

- Targeted Task 2 + notification + Agent suites: 72 passed. The first combined run emitted five
  TestClient cookie deprecation warnings; cookie setup was corrected and the final focused Task 2
  run passed 21 tests without warnings. The final matrix includes direct measurement timestamp
  staleness even when a station heartbeat still claims fresh/online.
- Historical route/Agent regression set: 61 passed, 26 failed due pre-v1 route response/behavior
  assertions; recorded in Task 2 status, not reported as pass.
- Ruff targeted: pass. Python `py_compile`: pass.
- Frontend `test:personalized-alerts`: pass; `test:api-base-url`: pass;
  `test:unified-legend`: 28/28; `test:email-snapshots`: 375/1280 pass; `npm run build`: pass.
- `docker compose config --quiet`: pass.
- Docker Desktop async profile build/start: pass after correcting the existing RabbitMQ anonymous
  volume cookie owner; no volume was deleted. PostgreSQL, RabbitMQ, Redis, backend, Agent, frontend,
  MQTT path, worker and Beat ran; health-checked services were healthy.
- Existing-volume migration smoke exposed that Compose had not listed migration 006. The
  `db-migrate` command now includes it; rerun exited 0 and direct PostgreSQL checks found all three
  tables plus `uq_predictive_warning_active_episode`.
- Live API smoke: 5/5 stations fresh/online; inhaled mass and clean-running route returned contract
  v1 with simulator provenance; route segment mass and duration sums exactly matched totals.
- Live security smoke: unauthenticated preference read 401, wrong CSRF 403, predictive opt-in changed
  independently and was restored. Manager dry-run was blocked by the real
  `forecast_threshold_not_crossed` gate.
- Live Celery/RabbitMQ/Redis smoke: normal evaluator completed with the same blocked reason. A
  separate integration rule and temporary verified opt-in produced one enqueue, immediate worker
  revalidation, `SUCCESS/not_configured/provider_disabled`, then `reused=1` on the duplicate with
  `attempt_count=1`. The recipient fixture was removed, the episode was expired, and backend/worker
  settings were restored to 50/100, `pm25-threshold-v1`, notifications false.
- PostgreSQL concurrency smoke made 16 parallel upserts for one fixture station/metric/rule; all
  returned one episode ID and the database contained one active row. The fixture was then expired.
- Backend Agent route smoke: the first request immediately after recreate hit the 8-second backend
  timeout; direct Agent then returned 200 in 1.79 seconds, and backend retry returned 200 in 7.59
  seconds with matching canonical route/map IDs, mass and `curated_demo_graph` provenance.
- Final rerun: Docker-targeted pytest `72 passed in 8.01s`; Ruff on changed Task 2 files passed;
  frontend personalized test and TypeScript/Vite build passed; email snapshots 375/1280 passed using
  the Docker Python fallback; Compose config passed. An expanded Ruff scan found 12 pre-existing
  F601 duplicate-key errors in unchanged `tests/test_agents/test_tools.py`.

## Contracts/risks changed

Added ADR 0019 and versioned API/domain/config/schema contract. Graph and forecast remain demo
baselines. Threshold wording is provisional, Resend acceptance is not delivery truth, and existing
historical route tests require a deliberate v1 migration rather than reintroducing forbidden
fallbacks/fields.

## Blockers/open questions

- Agent cold-start latency can exceed the backend's eight-second timeout for the first route request;
  warm retry passed but production readiness needs startup warmup or a separately reviewed timeout
  policy change.
- Decide separately whether historical POI-biased/multi-route Agent tests are retired or rewritten
  to `b7-personalized-alerts-v1`; do not change the v1 response to satisfy them.
- Threshold wording and graph freshness remain the documented demo risks; Resend provider acceptance
  still is not inbox-delivery truth.

## Next exact step

Review the Task 2 diff and decide whether Agent cold-start warmup belongs in a separate operational
change. Do not modify the v1 route contract to satisfy the legacy multi-route suite.

## Handoff IDs (request/message/proposal/job)

- Normal evaluator task: `65ebd801-cc4d-4c23-bee5-62371c5ab1b6` (blocked by live forecast gate).
- Closed integration episode: `c14422ca-8d24-408d-b4b9-b66bf0e8e6de`.
- Idempotent integration notification job: `2727d707-40ba-57ab-84ab-6d6c3ebb7e11`.
- Agent smoke request IDs: `task2-docker-agent-smoke` (cold timeout) and
  `task2-docker-agent-smoke-retry` (pass).
