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

- [ ] Test máy mới theo `docs/team-setup-and-demo.md`.
- [ ] Test clean startup và existing PostgreSQL volume.
- [ ] Test port 5173/5174 và Docker Desktop not running.
- [ ] Ghi blocker thật, không che bằng fixture.

### B2-QA-02 — Automated tests

- [ ] Compile backend/src/services.
- [ ] Chạy backend service/API tests.
- [ ] Chạy MQTT validator/simulator/device tests.
- [ ] Chạy frontend build.
- [ ] Cài đủ test dependency và chạy full pytest.
- [ ] Chạy `git diff --check`.

### B2-QA-03 — Failure/recovery rehearsal

- [ ] Backend down: station UI vẫn hiển thị error state đúng.
- [ ] Agent down: backend trả structured 503.
- [ ] MQTT restart: consumer reconnect.
- [ ] DB restart: không silently drop hoặc duplicate dữ liệu.
- [ ] Stale/offline: current/forecast/proposal bị chặn.
- [ ] Normal user gọi manager endpoint: 403.

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

1. Normal dashboard.
2. Spike -> active alert.
3. Agent grounded answer.
4. Proposal pending -> reject.
5. Proposal pending -> approve -> device ack.
6. Stale/offline/permission failure.

### B2-QA-05 — Release checklist

- [ ] `.env` không nằm trong Git diff.
- [ ] Không có secret/PII trong log/screenshot.
- [ ] `docker compose config --quiet` pass.
- [ ] Runbook khớp command thật.
- [ ] Task status được cập nhật.
- [ ] Leader review evidence.
- [ ] Mentor xác nhận các quyết định còn provisional.
