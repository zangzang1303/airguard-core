# AI Work Log

## Date / agent / machine

2026-08-24 / Codex / Thinkpad Windows workspace.

## Goal and outcome

Move AI-26, AI-27 and AI-28 to bounded deterministic social classification on Agent `:8001` and public API `:8000`, without an LLM or tools. Outcome: **Final PASS — 31 PASS, 0 FAIL, 1 BLOCKED**.

## Context read

`AGENTS.md`, Session 3D report, AI-25–32 test cases, social-classification diagnosis, backend conversation service and endpoint, Agent grounding/orchestration/router, API schemas, evaluator, relevant backend/Agent/API tests and Compose/build inputs.

## Files changed in Session 3E

- `backend/app/main.py`
- `backend/app/services/conversational_agent_service.py`
- `src/agents/policies/grounding.py`
- `src/agents/nodes/orchestration.py`
- `src/models/schemas.py`
- `src/api/routes.py`
- `tests/test_backend/test_conversational_agent.py`
- `tests/test_backend/test_social_endpoint_short_circuit.py`
- `tests/test_agents/test_grounding.py`
- `tests/test_api/test_routes.py`
- `eval/run_evaluation.py`
- `tests/test_agents/test_evaluation.py`
- `eval/golden_cases/airguard_agent_v1.jsonl`
- `specs/api-contracts.md`
- `docs/agent-evaluation.md`
- `docs/ai-chat-test-results-session-3e-2026-08-24.md`
- `.ai-log/2026-08-24-session-3e-social-classification.md`

The working tree already contained unrelated modified and untracked files. They were preserved. No stage, commit, revert or deletion was performed.

## Decisions

- Use a social-only Unicode/punctuation/whitespace normalizer so `PM2.5` remains intact for domain classification.
- Keep social phrases bounded rather than broad substring matching.
- Let explicit station/metric/environmental signals beat social language; station/map context alone is insufficient to force a domain route.
- Short-circuit social requests locally in the backend and before settings/provider initialization in the Agent graph.
- Remove the old social live-LLM rewrite path; social trace is locked to `deterministic_grounded` / `deterministic_social` with no provider/model metadata.
- Expose canonical `intent`, `conversation_kind`, `tool_arguments` and `map_actions` consistently on both API surfaces.
- Set the grounding policy literal to `2026-08-24.social-3e` and assert it literally in tests.
- Extend the strict evaluator to 62 cases with expected conversation kind and 3E zero-contract checks without lowering existing gates.

## Clean candidate evidence

- Agent: `C:\Users\Thinkpad\AppData\Local\Temp\p-074-agent-session-3e-ae6be3dc214e4393ad85b26dc9ef4d21`; 122 files; manifest `13404b9e78efdc6a29dd7f6e9321fbd6987b74b9198faf7183303637bb8e03ce`; image `sha256:c8db948fe555b8c0a7bfebb1d62f9e837ad03617bd6a9b934b28b0b4497e686f`.
- Backend: `C:\Users\Thinkpad\AppData\Local\Temp\p-074-backend-session-3e-ae6be3dc214e4393ad85b26dc9ef4d21`; 49 files; manifest `597f8699d819de0d5766a56c91ea1a7b016289e5dc35a1cdaf4cb9af914bd247`; image `sha256:84e64d8ce30b26c73bfa010c1fbdb401b1dee51af7732c479a10b025f56c024b`.
- Root legacy artifacts were excluded and retained their original hashes; see the Session 3E report.
- Import smoke, `pip check`, host-to-staging hashes, staging-to-image manifest digest and `sha256sum -c` passed.

## Tests and evaluator

- Focused backend social: 34 passed.
- Focused Agent routing/graph: 85 passed.
- Full backend: 208 passed in 21.49s.
- Full `tests/test_agents`: 167 passed in 25.48s.
- Strict evaluator: 62/62; every gate 100%; `release_gate_passed=true`; exit 0.
- `git diff --check`: exit 0 with only LF/CRLF conversion warnings.

## Runtime promotion

Promoted only the verified Agent and backend tags. Recreated exactly `backend agent` twice with `--no-deps --no-build --force-recreate`. Both recreations produced the expected Image IDs, healthy containers and passing running manifests. The final Agent status returned policy `2026-08-24.social-3e`.

PostgreSQL, MQTT, frontend, MQTT consumer, sensor simulator and device simulator were not restarted; their container IDs and `StartedAt` values were identical before and after the second recreate. No `docker cp`, bind mount, manual container edit or prune was used.

## Final probes

Required exact request IDs:

- AI-26: `session-3e-pass-AI26-8001`, `session-3e-pass-AI26-8000`
- AI-27: `session-3e-pass-AI27-8001`, `session-3e-pass-AI27-8000`
- AI-28: `session-3e-pass-AI28-8001`, `session-3e-pass-AI28-8000`

Additional request IDs cover punctuation, ellipsis, NBSP, repeated spaces, wellbeing with station/map context and domain precedence; all are in the Session 3E report. All 16 social probes had canonical social intent/kind, deterministic generation, zero tools/arguments/sources/proposals/map actions, no LLM metadata and no invented environmental fact. Both domain-precedence probes routed `current`, called `get_current_pm25` and resolved arguments/source to explicit `S03` despite conflicting `S01` context.

## Scope and handoff

No change was made to AI-24, map planner P1–4, forecast/recommendation algorithms, auth, HITL or DB. The one previously blocked case remains outside Session 3E scope.

Session 3E is complete. Running Agent and backend are the verified 3E images above; both are healthy. Full evidence is in `docs/ai-chat-test-results-session-3e-2026-08-24.md`.
