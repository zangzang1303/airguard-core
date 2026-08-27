# Backlog 2D — QA, Integration, DevOps và Evidence

## Cách tích checklist

- `[ ]` = chưa chạy/chưa đủ evidence.
- Đổi thành `[x]` khi người QA đã chạy lại được và lưu command/output.
- Không tích chỉ vì developer nói đã xong; QA cần xác nhận độc lập.
- Failure scenario phải ghi expected result, actual result và known limitation.

**Owner:** Thành viên QA/Integration  
**Mục tiêu:** biến implementation thành bằng chứng demo có thể replay.

## Nhiệm vụ

### B2-QA-01 — Environment smoke

- [x] Test máy mới theo `docs/team-setup-and-demo.md`.
- [x] Test clean startup và existing PostgreSQL volume.
- [x] Test port 5173/5174 và Docker Desktop not running.
- [x] Ghi blocker thật, không che bằng fixture.

Evidence: `docs/evidence/backlog2/b2-qa-01-2026-08-11.md`. Máy này được operator xác nhận là lần đầu chạy P-074; timestamp tạo volume mặc định và clean Compose replay được lưu để corroborate.

### B2-QA-02 — Automated tests

- [x] Compile backend/src/services.
- [x] Chạy backend service/API tests.
- [x] Chạy MQTT validator/simulator/device tests.
- [x] Chạy frontend build.
- [x] Cài đủ test dependency và chạy full pytest.
- [x] Chạy `git diff --check`.

Evidence: `docs/evidence/backlog2/b2-qa-02-2026-08-11.md`.

### B2-QA-03 — Failure/recovery rehearsal

Evidence: `docs/evidence/backlog2/b2-qa-03-2026-08-12.md`.

- [x] Backend down: station UI vẫn hiển thị error state đúng.
- [x] Agent down: backend trả structured 503.
- [x] MQTT restart: consumer reconnect.
- [x] DB restart: không silently drop hoặc duplicate dữ liệu.
- [x] Stale/offline: current/forecast/proposal bị chặn.
- [x] Normal user gọi manager endpoint: 403.

### B2-QA-04 — Evidence pack

Mỗi scenario lưu:

- command đã chạy;
- timestamp và branch/commit;
- container status;
- message/request/proposal/correlation ID;
- API response và DB query liên quan;
- screenshot UI nếu cần;
- known limitation.

Scenarios bắt buộc:

1. [x] Normal dashboard.
2. [x] Spike -> active alert.
3. [x] Agent grounded answer.
4. [x] Proposal pending -> reject.
5. [x] Proposal pending -> approve -> device ack.
6. [x] Stale/offline/permission failure.

Evidence: `docs/evidence/backlog2/b2-qa-04-2026-08-12.md`.

### B2-QA-05 — Release checklist

- [x] `.env` không nằm trong Git diff.
- [x] Không có secret/PII trong log/screenshot.
- [x] `docker compose config --quiet` pass.
- [x] Runbook khớp command thật.
- [x] Task status được cập nhật.
- [ ] Leader review evidence.
- [ ] Mentor xác nhận các quyết định còn provisional.

Evidence: `docs/evidence/backlog2/b2-qa-05-2026-08-12.md`. Technical checks pass 5/5; release sign-off vẫn chờ Leader và Mentor xác nhận, không được tự suy diễn là đã approved.
