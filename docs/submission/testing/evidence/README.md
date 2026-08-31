# Testing Evidence Index

## Evidence hiện tại

| Evidence | Vị trí | Ghi chú |
|---|---|---|
| Runtime verification 31/08 | [`runtime-verification-2026-08-31.md`](runtime-verification-2026-08-31.md) | Stack, pipeline, Agent, alert/recovery, offline gate, HITL/ACK/audit và scoped regressions tại `202037e`. |
| Browser E2E JSON/screenshots | [`../../../evidence/session-3f/`](../../../evidence/session-3f/) | 6/6 failure/recovery cases được tạo lại trên live stack. |
| Forecast benchmark | [`../../../evidence/forecast-model-evaluation.md`](../../../evidence/forecast-model-evaluation.md) | Tạo lại ngày 31/08/2026. |
| Agent evaluation criteria | [`../../../agent-evaluation.md`](../../../agent-evaluation.md) | Tiêu chí/golden gate. |
| Agent evaluation run | [`../../../../eval/reports/agent-evaluation-2026-08-08.md`](../../../../eval/reports/agent-evaluation-2026-08-08.md) | Filename legacy; kiểm tra trường Generated. |
| Historical UI report 24/08 | [`../../../ui-test-report-2026-08-24.md`](../../../ui-test-report-2026-08-24.md) | Agent UI issue đã được đóng bằng browser E2E 31/08. |

## Evidence còn cần

- [ ] Dashboard current/history khi đổi metric và time range.
- [ ] Forecast/Golden Window/timeline với thao tác Play/Pause.
- [ ] Personalized route/indoor fallback sau khi sửa `BUG-001`.
- [ ] PDF tiếng Việt, watermark, matrix và page breaks sau khi sửa `BUG-002`.
- [ ] Toàn bộ major views ở 375px và 1280px.
- [ ] Public URL incognito, HTTPS và CORS.
- [ ] Clean Agent image build không dùng dependency cache.

## Quy tắc evidence

- Ghi commit, timestamp, môi trường và tester.
- Che API key, token, password, email người nhận và dữ liệu cá nhân.
- Không dùng fixture cũ để chứng minh live pipeline hiện tại.
- Không chỉnh screenshot theo cách thay đổi ý nghĩa kết quả.
- ID rút gọn trong summary phải có bản đầy đủ trong runtime evidence.
