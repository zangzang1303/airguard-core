# Backlog 3 — Release và Integration Leader

**Owner:** Leader/Integrator
**Mục tiêu:** khóa một release candidate duy nhất, điều phối critical path và ngăn evidence bị thu trên
nhiều commit khác nhau.

## B3-REL-01 — Nhận bàn giao Backlog 2 và tạo baseline

- [ ] Review Definition of Done của bốn workstream Backlog 2 và link evidence tương ứng.
- [ ] Chọn main flow và optional HITL flow; ghi rõ feature nào bị deferred.
- [ ] Đồng bộ `main`, xác nhận working tree sạch và tạo release branch/tag candidate theo quy ước nhóm.
- [ ] Ghi commit SHA, ngày giờ, owner, Python/Node/Docker version vào release manifest.
- [ ] Kiểm tra không có `.env`, token, API key hoặc raw sensitive prompt trong diff.
- [ ] Đếm PR đã merge trên `origin/main`, lưu danh sách PR number/URL/merge SHA và xác nhận >=10.

**Preliminary evidence 12/08/2026:** local `origin/main` nhận diện 11 commit có subject
`Merge pull request #...`. Đây chưa phải final evidence; phải fetch/đối chiếu GitHub và lưu output
trên final release SHA trước sign-off.

**Acceptance:** có một RC0 duy nhất và mọi owner biết commit nào đang được kiểm thử.

## B3-REL-02 — Cấu hình provider và secret boundary

- [ ] Chốt một provider/model chính và một model name cụ thể cho demo.
- [ ] Thêm tên biến môi trường không chứa secret vào `.env.example`, README và Compose Agent service.
- [ ] API key chỉ nằm trong `.env` local/secret store; Agent không nhận DB/MQTT credentials.
- [ ] Startup fail rõ ràng hoặc readiness báo degraded khi cấu hình LLM bắt buộc bị thiếu.
- [ ] Đặt timeout, capped retry và giới hạn output/token phù hợp demo.

**Acceptance:** thay API key không cần sửa source; `docker compose config` không in giá trị secret vào
evidence được commit.

## B3-REL-03 — Gate 2 deliverable tracker

- [ ] MVP Demo video khoảng 3 phút: owner, script, release SHA và link có quyền xem.
- [ ] Architecture diagram: file nguồn, bản export nếu cần và reviewer xác nhận khớp runtime.
- [ ] Repo >=10 PR merged: PR list/URL/merge SHA trên `origin/main`.
- [ ] README: setup, env vars, sample queries và limitations được clean-machine review.
- [ ] Eval evidence: ít nhất 5 live LLM cases có input/output/provider/model/request ID/result.

**Acceptance:** tracker có owner, trạng thái và evidence link cho đủ 5 deliverables; không dùng
automated fixture report thay manual LLM evidence.

## B3-REL-04 — Contract freeze và change control

- [ ] Freeze API, MQTT, tool schema, proposal policy và frontend response contract sau RC1.
- [ ] Mọi fix sau freeze có issue/task, owner, affected tests và quyết định có chạy lại rehearsal hay không.
- [ ] Không merge refactor, formatting diện rộng hoặc feature ngoài main flow.
- [ ] Mỗi PR cần một reviewer và bằng chứng test liên quan.

**Acceptance:** không có contract drift giữa frontend, backend và Agent ở rehearsal cuối.

## B3-REL-05 — Final Gate 2 sign-off

- [ ] Xác minh automated test report, live eval, E2E trace, README, diagram và video cùng release SHA.
- [ ] Fetch remote rồi chạy PR evidence command; xác nhận >=10 PR merged và lưu PR URLs/merge SHAs.
- [ ] Kiểm tra video link bằng phiên trình duyệt không đăng nhập hoặc đúng permission submission.
- [ ] Kiểm tra `git status --short`, `git diff --check` và secret scan theo quy trình nhóm.
- [ ] Ghi known limitations, rollback/fallback và quyết định `GATE2-READY`, `PASS WITH LIMITATIONS`
      hoặc `BLOCKED`.

**Acceptance:** release manifest có SHA, link artifact, owner/reviewer và thời điểm ký trước deadline.
`PASS WITH LIMITATIONS` chỉ hợp lệ khi đủ năm deliverables; thiếu bất kỳ deliverable rubric nào phải
ký `BLOCKED`.

## Evidence bắt buộc

- `docs/evidence/release/<release-id>/manifest.md`
- Output test/build/Compose đã redact.
- Link PR list hoặc output Git chứng minh số PR merge.
- Link live eval report, E2E trace, architecture diagram và video.
