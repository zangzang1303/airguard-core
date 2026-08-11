# Backlog 3A — Release và Integration Leader

**Owner:** Leader/Integrator
**Mục tiêu:** khóa một release candidate duy nhất, điều phối critical path và ngăn evidence bị thu trên
nhiều commit khác nhau.

## B3-REL-01 — Nhận bàn giao Backlog 2 và tạo baseline

- [ ] Review Definition of Done của bốn workstream Backlog 2 và link evidence tương ứng.
- [ ] Chọn main flow và optional HITL flow; ghi rõ feature nào bị deferred.
- [ ] Đồng bộ `main`, xác nhận working tree sạch và tạo release branch/tag candidate theo quy ước nhóm.
- [ ] Ghi commit SHA, ngày giờ, owner, Python/Node/Docker version vào release manifest.
- [ ] Kiểm tra không có `.env`, token, API key hoặc raw sensitive prompt trong diff.

**Acceptance:** có một RC0 duy nhất và mọi owner biết commit nào đang được kiểm thử.

## B3-REL-02 — Cấu hình provider và secret boundary

- [ ] Chốt một provider/model chính và một model name cụ thể cho demo.
- [ ] Thêm tên biến môi trường không chứa secret vào `.env.example`, README và Compose Agent service.
- [ ] API key chỉ nằm trong `.env` local/secret store; Agent không nhận DB/MQTT credentials.
- [ ] Startup fail rõ ràng hoặc readiness báo degraded khi cấu hình LLM bắt buộc bị thiếu.
- [ ] Đặt timeout, capped retry và giới hạn output/token phù hợp demo.

**Acceptance:** thay API key không cần sửa source; `docker compose config` không in giá trị secret vào
evidence được commit.

## B3-REL-03 — Contract freeze và change control

- [ ] Freeze API, MQTT, tool schema, proposal policy và frontend response contract sau RC1.
- [ ] Mọi fix sau freeze có issue/task, owner, affected tests và quyết định có chạy lại rehearsal hay không.
- [ ] Không merge refactor, formatting diện rộng hoặc feature ngoài main flow.
- [ ] Mỗi PR cần một reviewer và bằng chứng test liên quan.

**Acceptance:** không có contract drift giữa frontend, backend và Agent ở rehearsal cuối.

## B3-REL-04 — Final release sign-off

- [ ] Xác minh automated test report, live eval, E2E trace, README, diagram và video cùng release SHA.
- [ ] Chạy `git log origin/main --merges` và lưu bằng chứng >=10 PR merged.
- [ ] Kiểm tra video link bằng phiên trình duyệt không đăng nhập hoặc đúng permission submission.
- [ ] Kiểm tra `git status --short`, `git diff --check` và secret scan theo quy trình nhóm.
- [ ] Ghi known limitations, rollback/fallback và quyết định `DEMO-READY` hoặc `BLOCKED`.

**Acceptance:** release manifest có SHA, link artifact, owner/reviewer và thời điểm ký trước deadline.

## Evidence bắt buộc

- `docs/evidence/release/<release-id>/manifest.md`
- Output test/build/Compose đã redact.
- Link PR list hoặc output Git chứng minh số PR merge.
- Link live eval report, E2E trace, architecture diagram và video.
