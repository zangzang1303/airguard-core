# Backlog 2 — Phân công hoàn thiện MVP

Backlog này là danh sách nhiệm vụ cần thực hiện sau khi core implementation đã có. Mục tiêu là
đóng các gap còn thiếu để chạy được demo end-to-end và có evidence báo cáo mentor.

## Cách phân công

Thay các tên trong bảng bằng tên thành viên thật của nhóm. Mỗi người tạo branch riêng, cập nhật
trạng thái task và gửi evidence khi hoàn thành.

| Workstream | Owner đề xuất | Phạm vi chính |
|---|---|---|
| Backend + Data/IoT | **Leader** | API, DB, MQTT pipeline, alert, HITL, audit, integration gate |
| Frontend + Figma | **Thành viên Frontend** | Chuyển screen Figma, gọi API thật, UX states, responsive |
| Agent/LangGraph | **Thành viên Agent** | Tool contract, grounding, proposal flow, safety evaluation |
| QA + DevOps + Evidence | **Thành viên QA/Integration** | Compose, smoke test, failure test, evidence pack, runbook |

## Quy tắc chung

1. Không commit `.env`, password, token hoặc API key.
2. Thay đổi API/MQTT/schema/tool phải cập nhật spec và test cùng commit.
3. Frontend không kết nối MQTT/DB trực tiếp.
4. Agent không truy cập DB/MQTT và không approve/reject proposal.
5. Simulator luôn gắn nhãn `source=simulator`/`is_simulated=true`.
6. Không đánh dấu DONE nếu chưa có command, output và evidence.

## Thứ tự thực hiện

```text
QA-01 setup runtime
  -> Leader BE/IoT trace MQTT-to-DB
  -> Leader alert/HITL/audit trace
  -> Agent evaluation
  -> Frontend Figma/API integration
  -> QA full rehearsal + evidence
```

## Definition of Done Backlog 2

- [ ] Full Compose startup thành công trên máy mới.
- [ ] S01-S05 đi qua simulator -> MQTT -> consumer -> PostgreSQL -> API -> UI.
- [ ] Alert spike/consecutive gate có evidence.
- [ ] Agent grounded và từ chối dữ liệu thiếu/stale/offline.
- [ ] Proposal pending -> manager approve/reject -> audit -> device ack/failure có trace.
- [ ] Màn hình trong scope Figma có component thật, loading/error/empty state.
- [ ] Unit/contract/integration/failure test và release evidence đã lưu.
- [ ] Mentor xác nhận các quyết định threshold, weather, station và device scope.

## Bàn giao sang Backlog 3

Sau khi toàn bộ Definition of Done ở trên được ký xác nhận, chuyển ngay sang
[Backlog 3 — Release MVP với LLM thật](../backlog3/README.md). Không chuyển task Backlog 2 còn lỗi
critical sang Backlog 3; mọi deferred item phải được ghi rõ và nằm ngoài main flow phát hành.
