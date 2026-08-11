# Backlog 1 — Integration/Demo

## Cách tích checklist

- `[ ]` = chưa chạy hoặc chưa có bằng chứng.
- Đổi thành `[x]` chỉ khi đã chạy đúng command trong môi trường Compose và lưu output.
- Một flow chỉ hoàn thành khi có đủ log/API/DB/UI evidence; không tích dựa trên mock.
- Ghi commit, thời gian, message/request/proposal/correlation ID và limitation.

**Owner:** Integration lead  
**Mục tiêu:** chứng minh toàn bộ luồng chạy lặp lại được trên Compose.

## INT-001 — Environment/Compose

- [ ] `docker compose config --quiet` pass.
- [ ] Start PostgreSQL/MQTT trước; chạy schema/seed; start service còn lại.
- [ ] `/health`, `/ready`, `/api/v1/stations`, Agent health pass.

## INT-002 — Normal data path

- [ ] S01–S05 hiển thị frontend.
- [ ] Trace được simulator -> MQTT -> consumer -> DB -> API -> UI.
- [ ] Source/freshness/status nhất quán giữa API, UI và Agent.

## INT-003 — Spike/alert path

- [ ] Chạy `SENSOR_SCENARIO=spike`.
- [ ] Chờ consecutive gate, xác nhận alert/dedupe/resolve.
- [ ] Lưu alert ID, message IDs và API/DB evidence.

## INT-004 — Agent path

- [ ] Current/history/compare/forecast query có tool evidence.
- [ ] Stale/offline/tool failure tạo refusal đúng.
- [ ] Proposal tạo pending, không tự approve.

## INT-005 — HITL/device path

- [ ] Manager approve/reject và optimistic version.
- [ ] Audit create/review/dispatch/failure.
- [ ] Approved command -> device simulator ack; rejected/pending không ack.

## INT-006 — Failure rehearsal/release

- [ ] Backend/Agent/MQTT/DB restart và reconnect.
- [ ] 401/403/409/503, empty/error/loading state.
- [ ] Full pytest/compile/frontend build pass.
- [ ] Evidence pack có command, timestamp, commit, IDs, output, screenshot và limitation.
- [ ] Leader review, mentor chốt threshold, station, weather, auth và device scope.

## Runbook

Thực hiện theo `docs/team-setup-and-demo.md`; lưu kết quả vào `.ai-log/` và dùng template
`templates/backend-data-iot-evidence-template.md`.
