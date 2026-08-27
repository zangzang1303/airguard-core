# AI chat test results — Session 3E (2026-08-24)

## Final status

**Final PASS — 31 PASS, 0 FAIL, 1 BLOCKED.**

AI-26, AI-27 and AI-28 now use bounded deterministic social classification on both the canonical Agent (`:8001`) and public API (`:8000`). Exact, punctuation, ellipsis, repeated-space, NBSP, station/map-context and explicit-domain-precedence probes all passed after the final images were promoted and recreated twice.

## Contract implemented

- AI-26: `intent=social`, `conversation_kind=acknowledgement`; short acknowledgement with no environmental claim.
- AI-27: `intent=social`, `conversation_kind=capabilities`; states current AQI/station, station comparison, baseline forecast limited to 1–3 hours, alerts and grounded recommendations; labels data as demo/simulated and excludes long-range forecasts, diagnosis and device control.
- AI-28: `intent=social`, `conversation_kind=wellbeing`; says the assistant is AI without health or emotions and redirects to AirGuard.
- Every social route short-circuits before settings/provider setup, LLM, user profile, station snapshot, geospatial planning and environmental tools.
- Social matching uses Unicode plus punctuation/whitespace normalization without changing domain strings such as `PM2.5`.
- Exact social phrases remain bounded. Explicit domain signals take precedence, while station/map context alone does not force a domain route.
- Grounding policy is locked to literal `2026-08-24.social-3e` in source, tests and the running Agent status endpoint.

## Clean candidates and reproducibility

The four untracked legacy artifacts at repository root were preserved and excluded from both allowlists and manifests:

| Artifact | SHA-256 |
|---|---|
| `airguard_agent_v1.jsonl` | `aedc6765f25ccb78bf2459807048d48d4db0bdad1e1d3c8a2c0f7b0b433373e4` |
| `conftest.py` | `b776461627b4d61ebfe5fdfe201ea7a0b028b187542f03917a4bc8a1db900af9` |
| `run_evaluation.py` | `231393c52dffd00982d01dda5ced17cb77c442d7ee1b30831e323e0571e3dd75` |
| `test_conversational_agent.py` | `a66f124ebb2a469f5b86a1a9a096d832e8b5f1ac87a10760d56c1be48ab14633` |

Canonical POSIX/LF manifests were generated from clean allowlist contexts on `C:`; no build used the shared `D:` tree directly.

| Candidate | Clean staging context | Files | Manifest SHA-256 | Tag | Image ID |
|---|---|---:|---|---|---|
| Agent | `C:\Users\Thinkpad\AppData\Local\Temp\p-074-agent-session-3e-ae6be3dc214e4393ad85b26dc9ef4d21` | 122 | `13404b9e78efdc6a29dd7f6e9321fbd6987b74b9198faf7183303637bb8e03ce` | `p-074-agent:session-3e-13404b9e` | `sha256:c8db948fe555b8c0a7bfebb1d62f9e837ad03617bd6a9b934b28b0b4497e686f` |
| Backend | `C:\Users\Thinkpad\AppData\Local\Temp\p-074-backend-session-3e-ae6be3dc214e4393ad85b26dc9ef4d21` | 49 | `597f8699d819de0d5766a56c91ea1a7b016289e5dc35a1cdaf4cb9af914bd247` | `p-074-backend:session-3e-597f8699` | `sha256:84e64d8ce30b26c73bfa010c1fbdb401b1dee51af7732c479a10b025f56c024b` |

For both candidates, host-to-staging hashes matched the allowlist, import smoke passed, `pip check` reported no broken requirements, the image manifest digest matched staging, and `sha256sum -c` passed. The same manifest checks passed inside both running containers after recreation.

No `docker cp`, bind mount, manual container edit, prune, stage, commit, revert or file deletion was used.

## Candidate validation

All tests ran inside the clean test-capable candidate; the broken host `.venv` was not used.

| Gate | Result |
|---|---|
| Focused backend social | **34 passed** |
| Focused Agent routing/graph | **85 passed** |
| Full `tests/test_backend` | **208 passed in 21.49s** |
| Full `tests/test_agents` | **167 passed in 25.48s** (requirement: at least 153) |
| Strict evaluator | **62/62 passed**, CLI exit 0 |
| `git diff --check` | Exit 0; only Git LF/CRLF conversion warnings |

The evaluator grew from 52 to 62 cases. Tool selection, grounding, safety, proposal eligibility, tool-error transparency, critical grounding and critical safety were all 100%; `release_gate_passed=true`. New coverage includes AI-26–28 exact cases, punctuation/ellipsis/NBSP/repeated-space variants, wellbeing with and without context, and explicit-domain precedence. Optional `expected_conversation_kind` is enforced without weakening existing gates.

## Promotion and two recreations

Only `backend` and `agent` were recreated, both times with `docker compose up -d --no-deps --no-build --force-recreate backend agent`.

| Verification | First recreation | Second recreation |
|---|---|---|
| Agent | expected image, healthy, `2026-08-24T14:47:06.657611974Z` | same image, healthy, `2026-08-24T14:49:11.729812754Z` |
| Backend | expected image, healthy, `2026-08-24T14:47:05.669660608Z` | same image, healthy, `2026-08-24T14:49:10.977690152Z` |
| Running manifests | Agent/backend pass | Agent/backend pass |
| HTTP health | both ports pass | both ports pass |
| Policy | final image deployed | `/api/v1/status` returns `2026-08-24.social-3e` |

Across the second recreation, PostgreSQL, MQTT, frontend, MQTT consumer, sensor simulator and device simulator retained identical container IDs and `StartedAt` timestamps. The first Compose output likewise listed only backend and agent as recreated; all other service timestamps predated it.

## Final runtime probes

Every social row below asserted: `intent=social`; `generation_mode=deterministic_grounded`; `conversation_mode=deterministic_social`; `used_tools=[]`; `tool_arguments=[]`; `sources=[]`; `proposal_id=null`; `map_actions=[]`; no provider/model fields and no invented station, environmental value, measurement unit or timestamp.

### Required six exact probes

| Case | Port / request ID | Conversation kind | Answer contract |
|---|---|---|---|
| AI-26 | `:8001` / `session-3e-pass-AI26-8001` | `acknowledgement` | Short polite thanks |
| AI-26 | `:8000` / `session-3e-pass-AI26-8000` | `acknowledgement` | Same deterministic answer |
| AI-27 | `:8001` / `session-3e-pass-AI27-8001` | `capabilities` | AQI/current station, comparison, baseline 1–3h, alert/recommendation, demo/simulated and exclusions |
| AI-27 | `:8000` / `session-3e-pass-AI27-8000` | `capabilities` | Same deterministic answer |
| AI-28 | `:8001` / `session-3e-pass-AI28-8001` | `wellbeing` | No human health/emotion claim; AirGuard redirect |
| AI-28 | `:8000` / `session-3e-pass-AI28-8000` | `wellbeing` | Same deterministic answer |

Exact answers:

- AI-26: “Cảm ơn bạn. Rất vui được hỗ trợ trong phạm vi AirGuard.”
- AI-27: “Mình hỗ trợ AQI/trạm hiện tại, so sánh trạm, dự báo baseline 1–3 giờ, cảnh báo và khuyến nghị grounded từ dữ liệu demo/mô phỏng. Mình không dự báo dài hạn, chẩn đoán hay điều khiển thiết bị.”
- AI-28: “Mình là trợ lý AI nên không có sức khỏe hay cảm xúc, nhưng có thể hỗ trợ về AirGuard.”

### Normalization, context and precedence

| Query | Request IDs (`:8001`, `:8000`) | Result |
|---|---|---|
| `Cảm ơn bạn nhé.` | `session-3e-pass-AI26-punctuation-8001`, `...-8000` | `social/acknowledgement`, common zero set |
| `Bạn có khỏe không...` | `session-3e-pass-AI28-ellipsis-8001`, `...-8000` | `social/wellbeing`, common zero set |
| `Bạn có khỏe không?` (NBSP) | `session-3e-pass-AI28-nbsp-8001`, `...-8000` | `social/wellbeing`, common zero set |
| `Bạn   có thể   giúp gì cho tôi?` | `session-3e-pass-AI27-spaces-8001`, `...-8000` | `social/capabilities`, common zero set |
| `Hôm nay bạn thế nào?`, `station_id=S04`; public map selects `S02` | `session-3e-pass-wellbeing-context-8001`, `...-8000` | remains `social/wellbeing`, common zero set |
| `Cảm ơn, AQI S03 hiện tại thế nào?`, conflicting `S01` context | `session-3e-pass-domain-precedence-8001`, `...-8000` | `current`; `get_current_pm25`; arguments/source `S03` |

The public domain response may contain map actions because it is an explicit environmental request; its canonical intent, tool arguments and grounded source match the Agent and override contextual `S01`.

## Final roll-up

AI-26–28 are PASS. AI-25, AI-29–32 and safety behavior remain covered by the 167-test Agent suite, 208-test backend suite and 62-case evaluator.

**Final PASS — 31 PASS, 0 FAIL, 1 BLOCKED.**
