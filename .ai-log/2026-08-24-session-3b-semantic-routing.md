# AI Work Log

## Date / agent / machine

2026-08-24 / Codex / Windows workspace `D:\Ai_Thuc_Chien\P-074`.

## Goal

Fix deterministic semantic/entity routing for AI-06, AI-08, AI-09, AI-11 and AI-22 without changing forecast, social, auth, HITL, backend database contracts or map planner.

## Context read

`AGENTS.md`, `README.md`, `tasks/ai-agent.md`, `docs/agent-evaluation.md`, ADR 0004, baseline/test-case reports, source routing/composer files and relevant Agent tests. Baseline HEAD: `b0837deffb77a0a71ab6e36e98ca81b7477ab21a`.

## Files changed

- `src/agents/policies/grounding.py`
- `src/agents/policies/spatial_response.py`
- `src/agents/response_composer.py`
- `src/api/routes.py`
- `tests/test_agents/test_grounding.py`
- `tests/test_api/test_routes.py`
- `docs/agent-evaluation.md`
- `docs/ai-chat-test-results-session-3b-2026-08-24.md`

## Decisions and rationale

- Reject an explicit request to invent AQI without evidence before any telemetry routing.
- Give station-scoped current component queries precedence over generic weather keywords.
- Resolve only canonical allowlist `VinUni -> S04`, confirmed in `data/stations.json` and `backend/db/schema.sql`; retain clarification for unknown entities.
- Use one bounded `compare_stations` call for AQI superlatives and compose the maximum AQI from that payload.
- Treat “sạch hơn” as a named-POI spatial comparison and label its grid result as spatial inference.

## Commands/tests run and results

- Captured five pre-change probes against both `:8001` and `:8000`; IDs and outcomes are in `docs/ai-chat-test-results-session-3b-2026-08-24.md`.
- `git diff --check`: pass (no whitespace errors).
- Host venv is broken, but Docker executable was supplied and used.
- Built `p-074-agent` image `sha256:5a4543a6bb1bb216008bc50243a42c4b8de426ad55a12820b153047c398c890e`.
- `docker compose run --no-TTY --no-deps ... python -m pytest -q tests/test_agents`: **136 passed in 17.15s**.
- Recreated only Agent: `docker compose up -d --no-deps agent`.
- Agent health/status passed; host/container `grounding.py` SHA-256 matched.
- Probed AI-06/08/09/11/22 through both `:8001` and `:8000`; all PASS. Full evidence is in the Session 3B report.

## Contracts/risks changed

No API, MQTT, database, forecast, auth, HITL or map-planner contract changes. `RouteDecision` adds internal `comparison_mode` and entity label only. `/api/v1/status` now imports the policy version rather than duplicating it. Public map-planner intent remains a P1-4 finding, not changed.

## Blockers/open questions

No blocker for Session 3B.

## Next exact step

Address P1-4 separately: reconcile public map-planner actions/provenance with canonical Agent intent without changing semantic routing contracts.

## Handoff IDs (request/message/proposal/job)

See the pre-change request IDs in `docs/ai-chat-test-results-session-3b-2026-08-24.md`.
