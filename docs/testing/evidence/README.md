# Testing evidence index

## Evidence hiện hành

- [`runtime-verification-2026-09-01.md`](runtime-verification-2026-09-01.md): regression 801 tests, frontend/browser retest, live route/indoor và offline forecast reproduction trên commit `aeda2ab`.
- [`runtime-verification-2026-08-31.md`](runtime-verification-2026-08-31.md): live pipeline, alert/recovery, HITL reject/approve, device ACK và audit chain trên commit `202037e`.
- [`../../../evidence/session-3f/browser_e2e_evidence.json`](../../../evidence/session-3f/browser_e2e_evidence.json): browser 503/timeout/network/recovery evidence và screenshots.
- [`../../../evidence/forecast-model-evaluation.md`](../../../evidence/forecast-model-evaluation.md): forecast benchmark.
- [`../../../../eval/reports/agent-evaluation-2026-08-08.md`](../../../../eval/reports/agent-evaluation-2026-08-08.md): Agent golden evaluation.

## Evidence còn thiếu

- [ ] Dashboard current/history multi-metric visual check.
- [ ] Forecast API/UI comparison.
- [ ] Timeline Play/Pause và heatmap visual check.
- [ ] PDF tiếng Việt, matrix và page-break inspection.
- [ ] Full responsive review 375/1280.
- [ ] Public URL incognito/HTTPS/CORS.
- [ ] Clean image build trên final commit.
- [ ] Dependency advisory disposition.

## Quy tắc evidence

- Ghi commit, thời gian, môi trường, command và actual result.
- Log/screenshot phải được làm sạch secret, token và PII.
- Historical evidence không thay thế retest trên final release commit.
- External provider chưa được gọi không được mô tả là delivery PASS.
