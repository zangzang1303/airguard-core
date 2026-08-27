# AI chat test results — Session 3D (2026-08-24)

## Outcome

**Final PASS — 28 PASS, 3 FAIL, 1 BLOCKED.**

AI-16–18 are grounded deterministic recommendations. The release gates, clean candidate manifests, two independent recreates, and six post-promotion probes are green.

No `docker cp`, bind mount, manual container edit, prune, DB/profile/schema mutation, or restart of a service other than `backend` and `agent` was used. Dynamic simulator readings were never compared across requests.

## Restored collateral workspace drift

The first staging workflow accidentally overwrote repository-root `requirements.txt` with the backend dependency file. Before restoring, `git diff -- requirements.txt` showed only that replacement; its SHA-256 equalled `backend/requirements.txt`: `9d0278c7e42c4d230a0390e85f92f44f3454ddb86cccdffd744b2c259fef90de`.

Root `requirements.txt` was restored exactly to the local HEAD content using `apply_patch` (no Git restore/reset/checkout). The final root SHA-256 is `7994056d76ca3c8e82b54c06cf8d6aed87431f1d931d34dbd486ea20b39a6cec`; it differs from backend and contains `pydantic-settings`, `langchain`, `langchain-openai`, `langgraph`, `pytest`, and `pytest-asyncio`. Backend requirements remain `9d0278c7e42c4d230a0390e85f92f44f3454ddb86cccdffd744b2c259fef90de`. `git diff -- requirements.txt` is empty.

Staging thereafter recorded both source hashes before copy, copied Agent requirements only from repository root and backend requirements only from `backend/requirements.txt`, verified every host-to-stage file hash, and verified that the root hash was unchanged after staging.

## Clean candidate evidence

| Image | Allowlisted runtime payload | Candidate tag / image ID | Manifest digest |
|---|---:|---|---|
| Agent | 92 files | `p-074-agent:session-3d-88f5ac57` / `sha256:8b303496ece62b3bb6d64e4fdf1a5eec8baba64964c5cc996e185cc5a3a28a4f` | `88f5ac57559991ad76664beba6a29400ab7fbc0db0bff7c0575ce3ccd212e755` |
| Backend (retained; not rebuilt) | 49 files | `p-074-backend:session-3d-916a0358` / `sha256:c16d71105cc1960cafcf0be53d1d4b56a0749dd6a09f83fa2d6202ab04f2ab39` | `916a035826768932e7603914a39a5e36322e86d843b58ba931dd3ecc38f627e7` |

Both manifests use lowercase SHA-256, two spaces, `./` POSIX paths, stable order, LF, UTF-8 without BOM, and exclude themselves plus Docker build-input files. Dockerfile and `.dockerignore` were separately hashed as build-input evidence. The Agent manifest is at `/app/BUILD_CONTEXT_MANIFEST.sha256`; the backend staging-only manifest is at `/app/app/BUILD_CONTEXT_MANIFEST.sha256` and covers only `requirements.txt` and `app/**` copied by its Dockerfile.

On the Agent candidate: import smoke for `langgraph`, `pytest`, `pytest_asyncio`, and `pydantic_settings` passed; `python -m pip check` returned `No broken requirements found`; and `sha256sum -c BUILD_CONTEXT_MANIFEST.sha256` completed with every entry `OK`. The retained backend candidate's `sha256sum -c app/BUILD_CONTEXT_MANIFEST.sha256` likewise completed with every entry `OK`.

## Candidate test gates

| Gate on `p-074-agent:session-3d-88f5ac57` | Final result | Exit |
|---|---:|---:|
| `python -m pytest -q tests/test_agents` | **153 passed in 4.48s** | 0 |
| `python eval/run_evaluation.py` | **52/52**, all seven gates **100%**, release gate true; p50 `13.249 ms`, p95 `21.648 ms` | 0 |
| `tests/test_backend/test_conversational_agent.py` plus directly related `tests/test_agents/test_recommendations.py` | **27 passed in 1.97s** | 0 |
| `git diff --check` | no whitespace errors (only working-tree CRLF warnings) | 0 |

The strict evaluator and golden cases were not weakened or rewritten to hide a failure.

## Promotion and recreate verification

Rollback images recorded before promotion:

- Agent: `sha256:79f3ff2e86c8acb8dacc3a7426a47f48850129115df28c3067e0b794a18b6ffd`
- Backend: `sha256:74466dc1678637cabec5b1918672a830a1b8b8ce9b9e0cde7ca618a8d48f1bdb`

Both candidates were tagged to the Compose names and only `backend` and `agent` were recreated using `docker compose up -d --no-deps --no-build --force-recreate backend agent`.

| Recreate | Agent running image / health | Backend running image / health | In-container manifest verification |
|---|---|---|---|
| First | `sha256:8b303496ece62b3bb6d64e4fdf1a5eec8baba64964c5cc996e185cc5a3a28a4f` / healthy | `sha256:c16d71105cc1960cafcf0be53d1d4b56a0749dd6a09f83fa2d6202ab04f2ab39` / healthy | Agent and backend: all manifest entries `OK` |
| Second (`--no-build`, force recreate) | same / healthy | same / healthy | Agent and backend: all manifest entries `OK` |

Both `:8001/health` and `:8000/health` returned HTTP 200 after each recreate.

## Six post-promotion runtime probes

All probes used station context `S03` and the existing backend demo personas. Each returned `intent=recommendation` and exactly this deterministic order:

`get_current_pm25 → get_weather_context → get_pm25_forecast → get_active_alerts → get_user_profile → compare_stations`

The evidence sources contain current and station-comparison simulator timestamps, weather timestamp/source, three future baseline-forecast timestamps/source, and `get_user_profile` provenance (`backend_user_profile`). Answers disclose the simulator/demo status and carry policy `2026-08-19.ai-003.v2`; no medical diagnosis or official-observation claim was made.

| Case | :8001 request ID | :8000 request ID | Verified grounded answer behavior |
|---|---|---|---|
| AI-16 resident/normal | `agent-647ba8f0-40d7-4884-b888-fafdee352f5b` | `1ad44316-bc53-4fe1-8ca2-527b32713491` | Normal-profile recommendation grounded in S03 current, weather, alerts, forecast, and station comparison. |
| AI-17 sensitive | `agent-ebf55cd2-a6d9-441a-9c47-0cb5e1d9149b` | `a83921d3-7192-435f-b300-dad85cfc7475` | Backend `sensitive` group governed conservative, non-diagnostic wording; self-description was not treated as profile authority. |
| AI-18 outdoor_sport | `agent-0ef79d45-ccd1-489b-860a-67ace2603442` | `ad886680-a7b3-46db-998a-4cb88ff7aad5` | Selected only the best future forecast point in the 1–3-hour baseline window and explicitly stated that the contract cannot evaluate all of today. |

Runtime checks asserted six-tool order and count, recommendation intent, at least six evidence sources, and the AI-18 `1–3 giờ` plus `toàn bộ hôm nay` limitation. Tool arguments are deterministic contract arguments covered by the candidate's strict/golden tests: station `S03`; weather `{}`; forecast `{station_id:S03, hours:3, metric:pm25}`; alerts `S03`; backend profile user ID; and compare stations `S01`–`S05`.

## Regression coverage

Exact and paraphrase golden coverage exists for AI-16–18, contradicted self-claimed-sensitive/normal profile, absent station, absent user, forecast outage, and profile outage. Missing required context fails closed with clarification and zero tools/sources/facts. The forecast is baseline PM2.5 only (1–3 hours), and no fallback LLM supplies missing evidence.
