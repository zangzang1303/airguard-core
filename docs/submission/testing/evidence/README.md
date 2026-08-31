# Testing Evidence Index

## Evidence đã có trong repository

| Evidence | Vị trí | Ghi chú |
|---|---|---|
| Forecast benchmark | [`../../../evidence/forecast-model-evaluation.md`](../../../evidence/forecast-model-evaluation.md) | Được tạo lại ngày 31/08/2026. |
| Agent evaluation criteria | [`../../../agent-evaluation.md`](../../../agent-evaluation.md) | Tiêu chí/golden gate. |
| Agent evaluation run | [`../../../../eval/reports/agent-evaluation-2026-08-08.md`](../../../../eval/reports/agent-evaluation-2026-08-08.md) | Runner cập nhật trường `Generated` ngày 31/08; filename là legacy. |
| Backlog 2 QA evidence | [`../../../evidence/backlog2/`](../../../evidence/backlog2/) | Evidence ngày 11–12/08; dùng tham khảo, không thay final retest. |
| Live evaluation reports | [`../../../evidence/release/`](../../../evidence/release/) | Các release run cũ; kiểm tra commit trước khi trích dẫn. |
| Session 3F failure screenshots | [`../../../evidence/session-3f/`](../../../evidence/session-3f/) | Failure/recovery evidence lịch sử. |
| UI report 24/08 | [`../../../ui-test-report-2026-08-24.md`](../../../ui-test-report-2026-08-24.md) | Có một UI Agent FAIL cần retest. |

## Evidence còn thiếu cho final commit

- [ ] `01-compose-services.png` — service/container status trên final stack.
- [ ] `02-health-readiness.png` — frontend, backend, Agent health/readiness.
- [ ] `03-dashboard-five-stations.png` — S01–S05, source và freshness.
- [ ] `04-station-history.png` — đúng station/metric/time range.
- [ ] `05-forecast-24h.png` — bounds, confidence, model/source.
- [ ] `06-golden-window-heatmap.png` — timeline và Golden Window/worst window.
- [ ] `07-agent-grounded.png` — used tools, source, timestamp.
- [ ] `08-agent-route.png` — route/evidence/map action sau khi route failures được xử lý.
- [ ] `09-agent-insufficient-data.png` — stale/offline/outage fail closed.
- [ ] `10-hitl-pending.png` — proposal ID/version và pending state.
- [ ] `11-hitl-decision-ack.png` — Manager decision, command ID và ACK.
- [ ] `12-audit-chain.png` — correlation IDs xuyên suốt.
- [ ] `13-report-exports.png` — cùng report ID/checksum ở Markdown/HTML/PDF.
- [ ] `14-responsive-ui.png` — viewport 375px và desktop.
- [ ] `15-public-url-incognito.png` — HTTPS/CORS trên URL cuối.

## Quy tắc evidence

- Tên file bắt đầu bằng test/evidence ID.
- Ghi commit, timestamp, môi trường và tester trong caption hoặc bảng kết quả.
- Che API key, token, password, email nhận và dữ liệu cá nhân.
- Không dùng fixture cũ để chứng minh live pipeline hiện tại.
- Không chỉnh sửa screenshot theo cách thay đổi ý nghĩa kết quả.
