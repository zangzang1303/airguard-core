# Backlog 1 — Backend

## Cách tích checklist

- `[ ]` = chưa thực hiện.
- Đổi thành `[x]` chỉ khi code đã chạy, test pass và có evidence ở cuối task.
- Nếu mới làm một phần, giữ `[ ]` và ghi `PARTIAL: ...` bên dưới task.
- Nếu bị chặn, ghi `BLOCKED: lý do + người cần hỗ trợ + bước tiếp theo`.

**Owner:** Backend lead  
**Mục tiêu:** FastAPI là system of record cho station, measurement, alert, approval, audit và jobs.

## BE-001 — API foundation

- [ ] `/health`, `/ready`, `/docs`, CORS và request/correlation ID.
- [ ] Error envelope gồm `code`, `message`, `request_id`, `details`; không lộ stack trace/secret.
- **Acceptance:** DB down làm `/ready` trả 503 có cấu trúc.
- **Evidence:** health/readiness output và log request ID.

## BE-002 — Station/current/history

- [ ] API stations, current, history, compare đọc PostgreSQL.
- [ ] Response có `source`, freshness, `status`, `is_stale`.
- [ ] 404 station, query hours 1–72 và station chưa có measurement.
- **Evidence:** API response của S01–S05 đối chiếu DB.

## BE-003 — Ingestion

- [ ] Typed schema, timezone/range/source validation.
- [ ] Idempotent theo `message_id`; duplicate trả kết quả rõ ràng.
- [ ] Invalid/future/stale/unknown station có reason code và không cập nhật current.
- **Evidence:** valid + reject matrix.

## BE-004 — Alert engine

- [ ] Threshold warning/critical, consecutive gate, dedupe/cooldown.
- [ ] Offline alert, resolve và audit.
- **Acceptance:** spike hai mẫu liên tiếp tạo đúng một active alert.

## BE-005 — HITL approval

- [ ] Proposal `pending`; evidence/station freshness gate.
- [ ] Manager-only approve/reject, optimistic version và 409 khi review cũ.
- [ ] Approve tạo command intent; reject không dispatch.

## BE-006 — Audit

- [ ] Append-only audit cho create/approve/reject/dispatch/failure/resolve.
- [ ] Query manager-only, correlation ID và metadata đã redact.
- **Evidence:** trace `proposal -> review -> dispatch -> outcome`.

## BE-007 — Jobs

- [ ] Job registry/idempotency và `/jobs/{task_id}`.
- [ ] `queued/running/succeeded/failed`, retry/timeout rõ ràng.
- [ ] Celery là optional; dependency thiếu phải trả lỗi hành động được.

## File và kiểm thử

`backend/app/`, `backend/db/`, `specs/api-contracts.md`, `tests/test_backend/`.

```powershell
python -m compileall -q backend/app
python tests/test_backend/test_services.py
python tests/test_backend/test_api_contract.py
```
