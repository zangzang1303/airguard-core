# AI Work Log

## Date / agent / machine
2026-08-04 / Codex / local workspace

## Goal
Implement AI-001: typed tool contracts, backend HTTP adapter, fake fixture adapter, registry docs, and contract tests for the AirGuard AI Agent.

## Context read
`AGENTS.md`, `tasks/ai-agent.md`, `specs/api-contracts.md`, `adrs/0004-agent-design.md`, current `src/agents/tools/`, `backend/app/main.py`.

## Files changed
- `src/agents/tools/contracts.py`
- `src/agents/tools/backend_client.py`
- `src/agents/tools/fake_adapter.py`
- `src/agents/tools/__init__.py`
- `tests/test_agents/test_tools.py`
- `docs/agent-tool-registry.md`

## Decisions and rationale
- Tool registry version is `2026-08-04.ai-001`, owner `ai-agent`.
- Inputs use strict Pydantic validation to block invalid station IDs, hours, user IDs, and proposal payloads before backend dispatch.
- Backend outputs allow additive fields but validate required environmental facts before LLM context.
- HTTP adapter maps validation, 404, 5xx, timeout, malformed JSON, and schema drift to typed `ToolError`.
- `create_warning_proposal` is mutating and is not retried by the adapter.
- `get_user_profile` and `create_warning_proposal` are contracted but backend endpoints are not implemented yet.

## Commands/tests run and results
- `ruff check src/agents/tools tests/test_agents/test_tools.py --fix`: fixed import/style issues.
- `ruff check src/agents/tools tests/test_agents/test_tools.py`: passed.
- `python -m py_compile src/agents/tools/contracts.py src/agents/tools/backend_client.py src/agents/tools/fake_adapter.py tests/test_agents/test_tools.py`: passed.
- Fake adapter smoke import/call: returned `True S01 simulator`.
- `pytest tests/test_agents/test_tools.py`: blocked during global conftest import because `langgraph` is not installed in the local environment.

## Contracts/risks changed
Added docs for the Agent tool registry and endpoint mapping in `docs/agent-tool-registry.md`. No API/backend behavior changed.

## Blockers/open questions
Install project dependencies, especially `langgraph`, before pytest collection can run through `tests/conftest.py`.

## Next exact step
Install/sync Python dependencies, then run `pytest tests/test_agents/test_tools.py`. After AI-001 is green, proceed to AI-002 grounding/routing.

## Handoff IDs (request/message/proposal/job)
No runtime request, proposal, or job IDs.

