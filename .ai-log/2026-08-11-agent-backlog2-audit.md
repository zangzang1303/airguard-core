# AI Work Log

## Date / agent / machine

2026-08-11 / Codex / Windows workspace `E:\Vinproject\P-074`

## Goal

Audit and complete `tasks/backlog2/agent-langgraph.md` sequentially, requiring a passing focused gate before moving from B2-AI-01 through B2-AI-04.

## Context read

`AGENTS.md`, `README.md`, `tasks/backlog2/agent-langgraph.md`, `tasks/ai-agent.md`, `specs/api-contracts.md`, `docs/agent-tool-registry.md`, `docs/agent-evaluation.md`, ADR 0003/0004/0006, and the Agent implementation/tests.

## Files changed

- Agent routing/composition: `src/agents/nodes/orchestration.py`, `src/agents/policies/grounding.py`, `src/agents/response_composer.py`.
- Tool contract/adapter/fixture: `src/agents/tools/contracts.py`, `src/agents/tools/backend_client.py`, `src/agents/tools/fake_adapter.py`.
- Regression tests: `tests/test_agents/test_tools.py`, `tests/test_agents/test_grounding.py`, `tests/test_agents/test_proposals.py`.
- Logging regression: `scripts/log_hook.py`.
- Evidence/docs: `docs/agent-tool-registry.md`, `docs/agent-evaluation.md`, `tasks/backlog2/agent-langgraph.md`, generated reports under `eval/reports/`.

## Decisions and rationale

- Safety decisions with a direct refusal must route to composition before proposal routing; this prevents HITL-bypass prompts from reaching the mutating node.
- Proposal requests without authenticated `user_id` clarify instead of guessing identity.
- Weather tool output now requires `is_fallback`; fallback answers explicitly state they are not live/official weather.
- Backend 401/403 maps to typed `permission_denied` rather than generic unavailability.
- Proposal traces expose the deterministic proposal policy version while preserving correlation through `request_id`.
- Codex normalization stores the prompt resolved from transcript JSONL; normalized shell transcripts are filtered before logging. The terminal detector now has its required compiled regex.

## Commands/tests run and results

- Tool contract gate: 20 passed after adding 403 and live active-alert filter coverage.
- Grounding/forecast/recommendation gate: 50 passed on final recheck.
- Proposal/backend contract gate: 29 passed on final recheck.
- Safety/evaluation focused gate: 69 passed on final recheck.
- `eval/run_evaluation.py`: 39/39 cases; tool selection, grounding, safety, proposal eligibility and error transparency all 100%.
- `ruff check src/agents tests/test_agents eval/run_evaluation.py`: passed.
- `pytest tests/test_agents tests/test_api -q`: 89 passed.
- Full `pytest -q`: 131 passed after adding the active-alert and Vietnamese HITL regressions.
- Docker live recheck after the fixes: PostgreSQL readiness returned 200; station API returned 5/5; frontend, backend and Agent health returned 200. `get_active_alerts` completed with `status=success`; the Vietnamese self-approval request returned `hitl_bypass/refused`, called no tools and created no proposal.

## Contracts/risks changed

Tool error contract adds `permission_denied` for backend 401/403. Weather contract requires explicit fallback provenance. Both are documented in `docs/agent-tool-registry.md`.

## Blockers/open questions

No known Agent blocker remains. The backend now performs the `status=active` alert gate before Agent output validation, and Vietnamese self-approval/rejection variants are refused before tool execution. AirGuard services are running on ports 8000/8001/5173.

## Next exact step

Create the Agent completion branch, commit the verified scope and push it to `origin`.

## Handoff IDs (request/message/proposal/job)

Fixture proposal: `proposal-001`; correlation regression: `req-create-failed`; live requests: `docker-smoke-current`, `docker-smoke-hitl`, `docker-port8000-final`; no live proposal/job created.
