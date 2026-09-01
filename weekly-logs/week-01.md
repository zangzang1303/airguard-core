# Mentor Duty — Tuần 1 — T-074

## Done

- Chốt hướng MVP: **AirGuard AI — AI Agent giám sát PM2.5 ngoài trời trong khu đô thị/campus giới hạn**.
- Xác định phạm vi chính: bản đồ thật, 5 điểm cảm biến PM2.5 giả lập qua MQTT và API thời tiết thực tế.
- Thống nhất In-scope/Out-of-scope, vấn đề, giải pháp đề xuất và mục tiêu SMART trong 6 tuần.
- Phác thảo kiến trúc gồm Sensor Simulator, MQTT Broker, FastAPI Backend, PostgreSQL, Forecast Service, AI Agent, React Leaflet Dashboard và HITL.
- Xác định Demo 1 tập trung vào luồng: Sensor Simulator → MQTT → Backend → Database → Map Dashboard.

## Doing

- Chọn khu vực bản đồ thật và 5 vị trí cảm biến PM2.5.
- Thiết kế database schema ban đầu cho `stations`, `measurements`, `weather_observations`, `alerts`, `users`, `approval_requests` và `devices`.
- Chuẩn bị backlog, user stories và phân công nhiệm vụ cho 4 thành viên.
- Chuẩn bị prototype ban đầu cho MQTT simulator và React Leaflet map.

## Blocked

- Cần thêm thời gian để thống nhất kiến trúc kỹ thuật cuối cùng giữa MQTT, backend, database, frontend map và AI Agent.

## Link code/demo

- [GitHub repository](https://github.com/AI20K-Build-Phase-Cohort-3/P-074)

## Câu hỏi cho Coach

- Demo 1 chỉ cần chứng minh luồng MQTT → Backend → Database → Map Dashboard có đủ không?

## Kế hoạch từ tuần trước

- Chốt phạm vi MVP và các chức năng nâng cao.
- Phân công nhiệm vụ cụ thể cho bốn thành viên.
- Tạo repository và quy ước làm việc với Git.
- Thiết kế cấu trúc thư mục của dự án.
- Thiết kế database lưu dữ liệu cảm biến, cảnh báo và lịch sử điều khiển.
- Xây dựng MQTT Simulator gửi dữ liệu PM2.5, CO₂, nhiệt độ và độ ẩm.
