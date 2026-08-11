# Backlog 3C — Frontend Demo Flow

**Owner:** Frontend lead
**Mục tiêu:** khóa một browser flow ổn định để người dùng nhập câu hỏi và thấy output LLM grounded từ
backend thật.

## B3-FE-01 — Agent Chat release integration

- [ ] `main.tsx` là entrypoint duy nhất của build; legacy JSX không được dùng ngầm.
- [ ] Agent Chat gọi backend canonical `POST /api/v1/agent/chat`, không gọi Agent service trực tiếp.
- [ ] Gửi user/station context theo contract và giữ request/correlation ID trong technical details.
- [ ] Hiển thị answer, used tools, source, observed time, freshness và simulator disclaimer.
- [ ] Không ghép thêm PM2.5/forecast/recommendation ở client.

**Acceptance:** prompt demo từ browser hiển thị đúng output của request hiện tại và evidence có thể mở
kiểm tra.

## B3-FE-02 — Loading và failure states

- [ ] Có sending/loading state và chặn double submit trong lúc request đang chạy.
- [ ] Xử lý validation, 401/403/422/503, network timeout và malformed Agent response.
- [ ] Provider/Agent/backend down hiển thị lỗi rõ, không fallback sang canned answer hoặc fake live data.
- [ ] Retry tạo request mới nhưng không nhân đôi proposal mutation.
- [ ] Keyboard focus, copy answer và mobile viewport không làm mất action quan trọng.

**Acceptance:** failure drill không hiển thị success hoặc environmental fact cũ.

## B3-FE-03 — Demo route lock

- [ ] Chọn tối đa ba prompt hiển thị sẵn hoặc ghi trong demo script.
- [ ] Dashboard -> Agent Chat hoàn thành trong không quá ba thao tác.
- [ ] Nếu quay HITL: pending proposal -> manager queue -> approve/reject -> audit dùng server state thật.
- [ ] Ẩn/defer screen ngoài scope nếu placeholder có thể làm hỏng câu chuyện demo.
- [ ] Chụp screenshot 1280px của dashboard, Agent answer và HITL/audit nếu có.

**Acceptance:** presenter chạy main flow hai lần liên tiếp không refresh dữ liệu bằng tay hoặc sửa request.

## B3-FE-04 — Build và browser smoke

- [ ] Cài dependency từ lockfile và chạy `npm.cmd --prefix frontend run build`.
- [ ] Kiểm tra console không có uncaught error trong main flow.
- [ ] Chạy smoke trên browser mục tiêu với Compose backend, không dùng dev fixture.
- [ ] Lưu screenshot có release SHA/request ID liên quan trong evidence pack.

**Acceptance:** production build exit 0 và main flow browser pass trên RC.
