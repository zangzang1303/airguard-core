# Mentor Duty — Tuần 2 — T-074

## Done

- Hoàn thành chuẩn hóa API contract giữa Frontend và Backend.
- Frontend đã gọi được các API chính từ Backend theo format thống nhất.
- Backend đã có các endpoint cần thiết cho luồng MVP cơ bản.
- Hoàn thành các task chính của AI Agent.
- Agent đã chạy được pipeline cơ bản:
  - Nhận câu hỏi người dùng.
  - Xác định intent.
  - Chọn và gọi tool phù hợp.
  - Nhận kết quả.
  - Tạo câu trả lời có evidence.
  - Lưu trace.
- Định nghĩa và triển khai các tool Agent chính.
- Hoàn thiện tài liệu API convention, Agent definition, Tool contract, Data definition, Metrics và Test plan.
- Xác định hướng kiểm thử cho các scenario: `normal`, `high_pm25`, `sudden_spike`, `sensor_offline`, `stale_data` và `invalid_data`.

## Doing

- Chuẩn bị Docker Compose cho các service:
  - Frontend.
  - Backend.
  - PostgreSQL.
  - Mosquitto.
  - Sensor Simulator.
- Kiểm tra lại luồng tích hợp Frontend → Backend → Agent → Database → MQTT.
- Chuẩn bị test end-to-end với database thật thay vì mock/in-memory data.
- Rà soát lỗi khi chuyển từ chạy local thủ công sang Docker.

## Blocked

- Cần kiểm tra migration/schema database đã khớp với API và Agent tool chưa.
- Cần xác nhận Mosquitto MQTT chạy đúng trong Docker Compose.
- Cần kiểm tra Sensor Simulator có publish dữ liệu vào MQTT khi chạy trong Docker không.
- Cần test lại Agent khi dữ liệu lấy từ PostgreSQL thật thay vì mock data.

## Link code/demo

- [GitHub repository](https://github.com/AI20K-Build-Phase-Cohort-3/P-074)

## Câu hỏi cho Coach

- Nhóm nên ưu tiên hoàn thiện Docker Compose trước hay hoàn thiện test E2E trên môi trường local trước?
- PostgreSQL cần có migration đầy đủ hay có thể dùng `schema.sql`/`seed.sql` cho MVP?

## Kế hoạch từ tuần trước

- Hoàn thiện và đồng bộ giao diện giữa Figma và sản phẩm thực tế.
- Bổ sung giao diện dành cho Admin.
- Tiếp tục phát triển AI Agent:
  - Kết nối intent với tool tương ứng.
  - Hoàn thiện luồng xử lý Agent.
  - Kiểm tra đầu ra, evidence và trace.
- Tiếp tục tích hợp frontend với backend và các API liên quan.
- Rà soát các trạng thái loading, error, empty, stale và sensor offline.
