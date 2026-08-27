# Backlog 3 — README, Architecture Diagram và Video

**Owner:** PM/Docs owner và presenter
**Mục tiêu:** đóng gói release thành bộ deliverables có thể setup, hiểu và chấm độc lập.

## B3-DOC-01 — README release-ready

- [ ] Viết quick start ưu tiên Docker Compose từ clone -> `.env` -> build/up -> health -> browser.
- [ ] Liệt kê env vars theo service, required/optional, default và secret handling.
- [ ] Dùng đúng tên runtime như `OPENAI_API_KEY`, model name, Agent/backend URLs; bỏ tên cũ gây nhầm.
- [ ] Thêm 3–5 sample queries và expected loại output/tool, không hard-code số PM2.5 dự kiến.
- [ ] Thêm cách chạy pytest, frontend build, Compose smoke và live manual eval.
- [ ] Link architecture diagram, demo video, eval evidence và known limitations.
- [ ] Nêu rõ mọi environmental data là simulator, không phải quan trắc chính thức/chẩn đoán y tế.

**Acceptance:** một thành viên không implement có thể làm theo README để chạy main flow mà không sửa source.

## B3-DOC-02 — Architecture diagram

- [ ] Tạo `docs/architecture-diagram.md` bằng Mermaid và tùy chọn export PNG cho slide/video.
- [ ] Thể hiện Sensor Simulator, MQTT, Consumer, PostgreSQL, Backend, React, LangGraph Agent và LLM provider.
- [ ] Vẽ data-flow arrows, HTTP/MQTT boundary và system-of-record ownership.
- [ ] Thể hiện Agent chỉ gọi backend tools; không truy cập DB/MQTT trực tiếp.
- [ ] Thể hiện proposal pending -> manager -> audit -> dispatcher/device simulator sau approval.
- [ ] Gắn nhãn simulator/fallback và trust boundary chứa secret.
- [ ] Review diagram với `docker-compose.yml` và runtime code trước khi freeze.

**Acceptance:** diagram mô tả đúng release, không dùng sơ đồ generic trong `docs/guide/` làm artifact dự án.

## B3-DOC-03 — Script và video khoảng 3 phút

- [ ] Viết script theo từng mốc thời gian và chốt presenter/operator.
- [ ] Quay trên final release SHA sau rehearsal pass; đóng notification và che mọi secret.
- [ ] 0:00–0:20: problem, simulator disclaimer và user goal.
- [ ] 0:20–0:50: dashboard/5 stations và data flow thật.
- [ ] 0:50–1:50: user input -> tools -> LLM output có source/time.
- [ ] 1:50–2:35: HITL pending/review/audit nếu stable; nếu deferred, show safety refusal rõ ràng.
- [ ] 2:35–3:00: architecture, value và known limitations.
- [ ] Upload, kiểm tra âm thanh/độ phân giải/permission và mở lại link từ phiên khác.

**Acceptance:** video chứng minh input -> processing -> meaningful output; không cắt ghép fixture thành live flow.

Video bắt buộc có ít nhất một request mà trace/evidence xác nhận `generation_mode=live_llm`, đúng
provider/model đã ghi trong release manifest. Deterministic fallback không đạt deliverable video.

## B3-DOC-04 — Submission pack

- [ ] Link repository và final commit/tag.
- [ ] Link video và architecture diagram.
- [ ] Link live eval report có ít nhất 5 cases.
- [ ] Bằng chứng >=10 merged PRs.
- [ ] Release manifest/sign-off và known limitations.
- [ ] Kiểm tra tất cả link trước 20:00 ngày 16/08 để còn buffer.
