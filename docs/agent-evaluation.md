# Agent Evaluation

## Response style contract (Phase 1)

The presentation contract is documented in
[`docs/ai-response-style-contract-v1.md`](ai-response-style-contract-v1.md).
It is a proposal for the next runtime phase and does not change the current API,
tool names, schemas, thresholds, or deterministic grounding behavior.

The Phase 1 acceptance checklist is:

- summary-first answers for current, compare, forecast and recommendation;
- evidence/details separated from the user-facing conclusion;
- explicit simulator/provider provenance without a blanket simulator label;
- intent-specific failure wording for clarification, stale/offline/invalid data,
  timeout, out-of-scope and HITL refusal;
- no generic LLM explanation suffix that adds no user-visible information;
- no new environmental facts, policy decisions or source IDs introduced by LLM
  rewriting.

These items are documentation/evaluation targets only. Runtime implementation and
snapshot tests are scheduled for Phase 2.

## AI-002 fixture gate

Focused tests live in `tests/test_agents/test_grounding.py` and use
`FakeBackendToolClient`, so they require neither a database nor an LLM provider.

The AI-002 release gate covers:

- intent and expected tool arguments for current, impact assessment, history, compare, weather, forecast, alert and profile;
- spatial POI comparison and wind-vector questions must call `get_spatial_air_quality`, preserve model/weather provenance and label geometric inference;
- mandatory tool use even when a user says not to call tools;
- source mapping for environmental facts from the same request;
- AQI-first current-station responses that enumerate PM2.5, CO₂, noise and temperature from the same fresh snapshot;
- transparent handling of backend outage, empty history, stale, offline, invalid and invalid arguments;
- rejection of missing freshness, timezone-less environmental timestamps, stale weather and stale forecast;
- baseline-only 1–3 hour forecast routing: AQI and PM2.5 retain backend metric, provenance, model,
  timezone-aware generation/forecast times, freshness, confidence and limitations; 24-hour/cả ngày
  requests are refused without calling a forecast tool;
- simulator/fixture transparency for current, history, compare, weather, forecast and alert answers;
- clarification for missing station context;
- multi-turn follow-up resolution from backend-validated semantic memory, with fresh tool calls,
  owner isolation, expiry and no-memory clarification;
- bounded social conversation for greeting, acknowledgement, wellbeing, capability and farewell;
- unknown short messages must clarify instead of falling through to environmental recommendation;
- social responses must short-circuit deterministically before LLM/tool/profile/geospatial access and have no tool arguments, sources, proposals or map actions;
- refusal of prompt injection, medical diagnosis, emergency claims, device control and HITL bypass;
- trace request id, tool status/latency, final outcome and PII/secret redaction.

## AI-006 golden-set gate

### Phiên 3B — semantic/entity routing (2026-08-24)

Regression coverage trong `tests/test_agents/test_grounding.py` xác nhận deterministic routing
cho snapshot đa chỉ số theo trạm, AQI superlative bằng đúng một `compare_stations` call, allowlist
`VinUni -> S04`, spatial comparison Sapphire/Ngọc Trai và direct refusal cho yêu cầu tự đoán khi
không có evidence. Các assertion kiểm tra intent, tool name và arguments; unknown entity vẫn phải
clarification và refusal không được gọi telemetry tool hay tạo environmental value.

Precedence được áp dụng theo thứ tự: refusal thiếu evidence, station-scoped current snapshot,
AQI superlative, rồi weather/spatial/recommendation. Allowlist chỉ là định danh tĩnh được đối
chiếu với `data/stations.json` và `backend/db/schema.sql`; không phải evidence môi trường.

### Station shorthand và AQI tốt nhất (2026-08-26)

Router coi một mã trạm độc lập như `S01` hoặc `Trạm S01 đang thế nào?` là yêu cầu snapshot hiện
tại và gọi `get_current_pm25` cho đúng trạm. Câu hỏi `Trạm nào đang có chỉ số tốt nhất?` được hiểu
theo chỉ số tổng quan AQI-first: gọi đúng một `compare_stations` cho S01-S05, sau đó composer chọn
trạm có AQI thấp nhất từ payload valid/fresh cùng request. Không có trạm mặc định và không tự tạo
giá trị AQI khi tool lỗi hoặc dữ liệu stale/offline/invalid.

Giai đoạn 1 mở rộng deterministic intent lexicon cho các cách nói tự nhiên như `ra sao`, `tình hình`,
`xu hướng`, `diễn biến`, `vượt ngưỡng`, `ổn nhất/sạch nhất`, `tốt hơn`, `đối chiếu`, `giờ nữa`,
`phù hợp để chạy bộ` và `nên tránh hoạt động ngoài trời`. Các cụm này chỉ ảnh hưởng chọn intent;
mọi tham số vẫn bị giới hạn bởi station allowlist, tool schema và data-quality gate.

### Giai đoạn 2 — semantic routing có kiểm soát (2026-08-27)

Khi deterministic router trả `clarification` hoặc `out_of_scope` không liên quan safety/social,
Agent có thể thử semantic router với deadline 2 giây. Provider phải trả JSON đúng schema gồm intent,
station ids, horizon/metric tùy intent, confidence và cờ clarification. Validator từ chối JSON lỗi,
extra keys, station ngoài S01-S05, tổ hợp field sai, confidence dưới `0.8` hoặc station không xuất
hiện trong request/context đã xác thực. Route hợp lệ được dựng lại thành `RouteDecision` và đi qua
allowlist/tool/data-quality gate hiện có; provider không bao giờ trả số AQI/PM2.5, timestamp hoặc
tool name. Nếu provider không cấu hình, timeout hoặc vi phạm schema, hệ thống giữ clarification
deterministic. Trace ghi `routing_mode=semantic` và confidence, không ghi raw prompt.

The executable golden set is `eval/golden_cases/airguard_agent_v1.jsonl`. It contains 41 cases for
current, history, compare, weather, forecast, alert, profile, recommendation, proposal/no-proposal,
spatial comparison/wind analysis, no-data, stale/offline/invalid data, backend/tool failure, injection, and medical/device/HITL
refusal. Every case defines expected intent, tools, arguments, allowed facts, forbidden claims, and
proposal expectation.

Metrics: tool-selection pass, fact-to-tool grounding pass, safety pass, proposal eligibility pass,
tool-error transparency, p50/p95 latency. Critical target: 100% grounding and safety on demo cases.
Store request trace/fixture version; redact secrets/PII. Any ungrounded environmental fact blocks
demo until its regression test passes.

Run the deterministic evaluation without a database or LLM provider:

```powershell
.\.venv\Scripts\python.exe eval\run_evaluation.py
```

The runner writes Markdown and JSON reports to `eval/reports/`. The baseline rerun on 2026-08-11 has
More than 52 cases and 100% tool selection, grounding, safety, proposal eligibility and tool-error
transparency. Recommendation graph integration is covered by the same deterministic fixture gate.

## Production chat live-stack evidence (P0)

Production chat no longer calls an LLM for social requests or deterministically routed domain
requests. `eval/run_live_evaluation.py` now verifies the canonical backend path with
`generation_mode=deterministic_grounded` and `llm_call_count=0`, alongside the existing tool,
grounding, safety/HITL, simulator-transparency and request-latency checks. It does not read a
provider key. Any live provider probe must invoke the provider adapter outside the production chat
endpoint.

The provider-backed procedure and results below are retained as historical pre-P0 evidence only;
they are not the current production chat release gate.

## Historical live LLM evidence (pre-P0 Gate 2)

> Historical record only. Do not rerun the commands in this section: the script has been
> repurposed as the provider-free production-chat gate described above.

The deterministic report above is a regression gate; it does not count as live-provider evidence.
With the Docker stack healthy, fresh simulator data available, and `OPENAI_API_KEY` configured only
in the local environment, run:

```powershell
.\.venv\Scripts\python.exe eval\run_live_evaluation.py
```

For the AgentRouter/Claude gate used in Backlog 4, configure `AGENTROUTER_API_KEY` and
`AGENTROUTER_MODEL`, then run:

```powershell
.\.venv\Scripts\python.exe eval\run_live_evaluation.py --expected-provider agentrouter --max-p95-ms 5000
```

For Gemini 3.6 Flash, configure `GEMINI_API_KEY` and run:

```powershell
.\.venv\Scripts\python.exe eval\run_live_evaluation.py --expected-provider gemini --max-p95-ms 5000 --case-delay 1
```

Gemini áp quota theo Google Cloud project, không theo từng API key. Kết quả
`provider_daily_quota_exhausted` nghĩa là quota ngày của project/model đã hết; không rerun bộ
release cho đến khi quota reset hoặc project được nâng tier. Rate limit ngắn hạn sẽ tuân theo
`RetryInfo` của Google với exponential backoff có giới hạn.

The runner calls the canonical backend endpoint (`POST /api/v1/agent/chat`) for LIVE-01 through
LIVE-05 and writes a sanitized JSON and Markdown pack under
`docs/evidence/release/<date>-<git-sha>/`. It records input, expected and actual tools, source/tool
references, provider/model, LLM and request latency, output, request ID and PASS/FAIL. A case only
passes with `generation_mode=live_llm`; missing keys, an unavailable stack, deterministic fallback,
or any contract mismatch produces `BLOCKED` and a non-zero exit code rather than fabricated evidence.
The demo release gate requires nearest-rank provider-latency P95 below 5 seconds and checks
station/source/simulator transparency terms for the three environmental-answer cases. The
production performance target remains P95 below 2.5 seconds; a demo result between 2.5 and
5 seconds is reported as `PASS WITH LIMITATIONS`, not full production readiness. The evaluator
returns exit code zero for both `PASS` and `PASS WITH LIMITATIONS`; `BLOCKED` still returns a
non-zero exit code.

### OpenAI-compatible demo rerun — 26/08/2026

The five-second demo profile was applied to three independent `openai/gpt-4o` runs through the
configured OpenAI-compatible endpoint:

- `phase4-demo5s-1`: `PASS WITH LIMITATIONS`, 5/5 live cases, P95 `4069.266 ms`;
- `phase4-demo5s-2`: `BLOCKED`, 4/5 live cases, one `provider_deadline_exceeded`;
- `phase4-demo5s-3`: `BLOCKED`, 2/5 live cases, three `provider_deadline_exceeded` outcomes.

The threshold change therefore makes a fully successful sub-five-second run demo-acceptable, but
does not hide provider instability. The demo release remains blocked until the required repeated
runs contain no timeout, deterministic fallback, HTTP error, or contract mismatch.

### Direct endpoint rerun — 26/08/2026

After switching the local `OPENAI_BASE_URL` to the direct OpenAI-compatible endpoint and recreating
only the Agent container, three independent batches produced:

- `phase4-direct5s-1`: 5/5 live cases, P95 `3880.944 ms`, `PASS WITH LIMITATIONS`;
- `phase4-direct5s-2`: 5/5 live cases, P95 `2017.858 ms`, `PASS`;
- `phase4-direct5s-3`: 5/5 live cases, P95 `2493.678 ms`, `PASS`.

The direct endpoint is materially faster and all cases were `live_llm` without timeout or fallback.
Because one of the three batches remained above the 2.5-second production target, aggregate status
is `PASS WITH LIMITATIONS` for demo readiness, not a full production latency sign-off.

### Stage 1 staging gate — 26/08/2026

After the direct endpoint was loaded into the Agent container, the staging gate ran three sequential
five-case batches:

- `stage1-2026-08-26-batch1`: `PASS`, 5/5, P95 `2010.283 ms`;
- `stage1-2026-08-26-batch2`: `PASS`, 5/5, P95 `1849.762 ms`;
- `stage1-2026-08-26-batch3`: `PASS WITH LIMITATIONS`, 5/5, P95 `4745.506 ms`.

Stage 1 is accepted for demo/staging because all three batches were `live_llm`, had no timeout or
fallback, and stayed below the five-second demo ceiling. This is not a production latency sign-off;
the third batch exceeded the 2.5-second production target.

## Phase 2 staging hardening — 26/08/2026

- Fault/grounding/tool/recommendation/proposal/API/security regression: `185 passed`; focused
  security/RBAC and API timeout contracts: `14 passed`.
- Bounded staging load probe (`2 workers × 3 rounds`, 6 requests): all 6 were `live_llm`, HTTP 200,
  no fallback/error; P50 `1774.936 ms`, P95/P99 `2999.491 ms`.
- Evidence: `docs/evidence/release/stage2-load-probe-c2-r3.json`; implementation:
  `eval/run_load_probe.py` with unit coverage in `tests/test_scripts/test_load_probe.py`.
- This is `PASS WITH LIMITATIONS` for staging only. It is not a production load sign-off; a
  production-scale load harness and provider metrics/alerting remain required.

### Phase 2 gate results — 26/08/2026

- Expanded load probe: concurrency 1 (`3` requests) stayed below the demo ceiling with P95
  `4590.232 ms`; concurrency 2 (`6` requests) had no error/fallback but P95 `5376.789 ms`;
  concurrency 4 (`8` requests) had no error/fallback but P95 `6858.381 ms`. Concurrency 2 and 4 are
  therefore `BLOCKED` by the five-second latency ceiling.
- Provider fault matrix passed timeout, 429, 503 and malformed-response cases with deterministic
  grounded fallback and sanitized failure codes: `docs/evidence/release/stage2-fault-matrix.json`.
- `GET /api/v1/metrics` now exposes bounded aggregate latency/fallback/failure counters and SLO
  alerts without prompts, IDs, sources, tokens or PII. This process-local window resets on restart;
  production multi-replica aggregation remains deployment work.
- Rollback rehearsal passed between pinned local images. The rollback image recovered health and
  metrics in `0.7s`, and the final image was promoted again without restarting backend, DB or MQTT.

Phase 2 is `PASS WITH LIMITATIONS`: fault handling, process-level metrics and rollback are covered,
but the production rollout remains blocked because concurrency 2+ breaches the demo P95 ceiling.

> Historical pre-P0 note: the former explanation deadline and live-provider release gate were
> removed from production chat. The only optional provider path is semantic routing, which uses its
> own bounded deadline and zero application-level retries.
