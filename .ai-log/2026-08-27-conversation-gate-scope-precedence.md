# AI Work Log

## Date / agent / machine

2026-08-27 / Codex / local workspace

## Goal

Align the public AI-chat conversation gate with the prescribed deterministic
preprocessing order: scope-only requests must stop before profile, telemetry,
map planning, or LLM access.

## Context read

`AGENTS.md`, `README.md`, `tasks/ai-agent.md`, `specs/api-contracts.md`,
`adrs/0004-agent-design.md`, `adrs/0012-bounded-social-conversation.md`, and
the existing AI-chat diagnosis/evaluation documents.

## Files changed

- `backend/app/main.py`
- `backend/app/services/conversational_agent_service.py`
- `tests/test_backend/test_conversational_agent.py`

## Decisions and rationale

- Added `out_of_scope` to the public endpoint's deterministic short-circuit.
  The previous gateway recognized this intent but still performed the domain
  profile/telemetry/Agent flow.
- Moved scope detection ahead of domain/location recognition. Location words
  such as `Ocean Park` and `Sapphire` must not convert restaurant/property
  requests into environmental queries.
- Replaced substring scope matching with phrase-boundary matching and removed
  the standalone `thuoc` signal. This preserves the environmental advice path
  for `toi thuoc nhom nhay cam` while retaining explicit medicine signals.
- Added a deterministic identity reply for `ban bao nhieu tuoi` and removed
  generic `bao nhieu` context inheritance. The standalone normalized `bao`
  weather signal was also removed because it collided with `bao nhieu`.

## Commands/tests run and results

- `.\.venv\Scripts\python.exe -m pytest tests/test_backend/test_conversational_agent.py tests/test_agents/test_grounding.py -q`
  - PASS: 120 tests. Pytest could not update `.pytest_cache` due to workspace
    permissions; this did not affect test execution.
- `.\.venv\Scripts\ruff.exe check backend/app/main.py backend/app/services/conversational_agent_service.py tests/test_backend/test_conversational_agent.py`
  - PASS.
- `git diff --check`
  - PASS.

## Contracts/risks changed

The chat request contract now accepts an optional bounded `conversation` list
of at most six visible `user`/`assistant` turns. It is used solely for explicit
anaphoric follow-ups, never as environmental evidence, and is excluded from
Agent trace data. No MQTT or database contract changed.

## Blockers/open questions

The requested bounded semantic-router design is not yet implemented as a live
structured LLM routing step. Existing deterministic routing remains the source
of intent/tool arguments and safely clarifies unknown requests. Frontend Vite
build is blocked in this workspace because Vite cannot create a temporary file
under `frontend/node_modules/.vite-temp` (`EPERM`).

## Next exact step

Create a typed bounded semantic router that is invoked only for deterministic
clarification outcomes, validates allow-listed station IDs and 1-3 hour
horizons locally, and falls back to clarification on any provider/JSON/error
condition. Then remove the remaining duplicated geospatial intent logic.

## Handoff IDs (request/message/proposal/job)

None.
