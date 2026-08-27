# AI Work Log — Phase 2 staging hardening

## Scope

Thực hiện các gate không thay đổi API/schema/runtime contract: fault/grounding/security regression,
load probe nhẹ, kiểm tra health và redaction.

## Results

- Agent/backend health: `ok`; stack staging healthy.
- Runtime provider (non-sensitive config): `openai/gpt-4o` qua
  `https://direct.shopaikey.com/v1`; API key không được đọc/in.
- Fault/grounding/tool/recommendation/proposal/API/security suite: `185 passed`.
- Security/RBAC + API timeout contract subset: `14 passed`.
- Staging load probe (`2 workers x 3 rounds`, 6 requests): `PASS`.
  - `live_llm_requests=6`, `non_live_requests=0`, `http_errors=0`.
  - P50 `1774.936 ms`, P95/P99 `2999.491 ms`, max `2999.491 ms`.
  - Evidence: `docs/evidence/release/stage2-load-probe-c2-r3.json`.
- Load probe unit test: `1 passed`; Ruff and `git diff --check` pass on new files.
- Expanded gated load runs (P95 ceiling `<5000 ms`):
  - concurrency 1, 3 requests: previous run P95 `4590.232 ms`, below ceiling;
  - concurrency 2, 6 requests: `BLOCKED`, 5/6 live, 1 HTTP/error, P95 `8450.828 ms`;
  - concurrency 4, 8 requests: `BLOCKED`, 8/8 live and no HTTP error, but P95 `6625.217 ms`.
- Provider fault matrix: `PASS` for timeout, 429, 503, malformed response and success. Failure
  cases remained `deterministic_grounded` with sanitized failure codes. Evidence:
  `docs/evidence/release/stage2-fault-matrix.json`.
- Added bounded aggregate Agent metrics at `GET /api/v1/metrics`: request/generation counts,
  sanitized failure counts, fallback rate, P50/P95/P99 and SLO alerts. It stores no prompt, user ID,
  source, token or PII and resets on process restart.
- Rollback rehearsal used pinned image tags without restarting backend/DB/MQTT. Rollback image
  `sha256:bc8ad151a7829a4a06cb827b3ee42685d9cde229feb55c42a7b4ec8fd7217c20` recovered health/metrics
  in `0.7s`; final image `sha256:5f3d11df35b965ef561d10cb98c59206c142ab44ae26a9fb2abf6407d633103f` was promoted again.
- Expanded load gate:
  - concurrency 1, 3 requests: P95 `4590.232 ms`, below demo ceiling;
  - concurrency 2, 6 requests: no error/fallback, P95 `5376.789 ms`, gate `BLOCKED`;
  - concurrency 4, 8 requests: no error/fallback, P95 `6858.381 ms`, gate `BLOCKED`.
- Provider fault matrix: `PASS` for timeout, 429, 503, malformed response and success. Failure
  cases remained `deterministic_grounded` with sanitized failure codes. Evidence:
  `docs/evidence/release/stage2-fault-matrix.json`.
- Added bounded aggregate Agent metrics at `GET /api/v1/metrics`: request/generation counts,
  sanitized failure counts, fallback rate, P50/P95/P99 and SLO alerts. It stores no prompt, user ID,
  source, token or PII and resets on process restart.
- Rollback rehearsal used pinned image tags without restarting backend/DB/MQTT:
  - rollback image `sha256:bc8ad151a7829a4a06cb827b3ee42685d9cde229feb55c42a7b4ec8fd7217c20`;
  - final image `sha256:5f3d11df35b965ef561d10cb98c59206c142ab44ae26a9fb2abf6407d633103f`;
  - rollback health/metrics recovered in `0.7s`, then final image was promoted again.
- Runtime metrics after the final probes: `total_requests=14`, `fallback_rate=0.0714`, P95
  `8087.363 ms`, alerts `agent_fallback_detected` and `provider_latency_demo_slo_breached`.
  The load blocker is therefore visible through monitoring rather than hidden.

## Limitations / blockers

- Load harness đã chạy concurrency 1/2/4 nhưng số mẫu vẫn giới hạn để tránh gây tải provider thật;
  concurrency 2/4 vượt demo P95 ceiling.
- Fault-injection HTTP trực tiếp qua PowerShell bị dừng ở lớp request validation (`422`) do encoding/
  payload, chưa tạo được provider-timeout evidence qua endpoint cô lập. Các failure path nội bộ vẫn
  được bao phủ bởi 185 regression tests; không dùng probe `422` để kết luận provider.
- P95 load `~3.0s` đạt demo ceiling 5s nhưng chưa đáp ứng production target 2.5s.
- Metrics hiện là process-local diagnostic; chưa có backend/dashboard production để aggregate nhiều
  replica và gửi cảnh báo ra ngoài.

## Decision

Phase 2 chưa được ký production-ready. Fault handling, metrics và rollback rehearsal đạt, nhưng
load gate bị `BLOCKED` từ concurrency 2 do timeout/P95 vượt 5 giây. Cần provider capacity,
backpressure/rate-limit hoặc tối ưu latency, cùng metrics aggregation/alert delivery production
trước rollout.
