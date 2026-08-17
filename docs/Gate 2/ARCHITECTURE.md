# Kiến trúc hệ thống AirGuard AI

## Tổng quan

AirGuard AI là MVP giám sát chất lượng môi trường tại 5 trạm mô phỏng S01-S05. Dữ liệu cảm biến đi qua MQTT, được kiểm tra và lưu trong PostgreSQL; FastAPI là nguồn dữ liệu duy nhất cho dashboard, AI Agent và quy trình phê duyệt.

AI Agent chỉ diễn giải dữ liệu đã được backend cung cấp qua tool. Agent có thể tạo đề xuất cảnh báo ở trạng thái `pending`, nhưng không thể tự phê duyệt, truy cập trực tiếp PostgreSQL/MQTT hoặc gửi lệnh thiết bị.

> Toàn bộ dữ liệu trong MVP có `source=simulator`; đây không phải hệ thống quan trắc chính thức.

## Ảnh sơ đồ

Các ảnh xuất bản dùng trong tài liệu nằm trong thư mục [`image/`](image/):

- [Kiến trúc tổng thể](<image/Kiến trúc tổng thể.png>)
- [Luồng AI Agent](<image/Luồng AI Agent.png>)
- [Luồng cảnh báo và phê duyệt](<image/Luồng cảnh báo và phê duyệt.png>)

## Sơ đồ kiến trúc

![Sơ đồ kiến trúc tổng thể](<image/Kiến trúc tổng thể.png>)

## Luồng dữ liệu chính

### 1. Thu thập dữ liệu cảm biến

1. `Sensor Simulator` tạo dữ liệu PM2.5, CO2, tiếng ồn và nhiệt độ cho S01-S05, sau đó publish lên các MQTT topic measurement/status.
2. `MQTT Consumer` nhận payload, kiểm tra schema, thời điểm đo, tính hợp lệ và freshness.
3. Payload hợp lệ được lưu vào PostgreSQL. Backend tính AQI, cập nhật trạng thái trạm, alert và dữ liệu phục vụ forecast.
4. React Dashboard gọi REST API của FastAPI để hiển thị bản đồ, chỉ số hiện tại, lịch sử, cảnh báo và dự báo 1-3 giờ. Frontend không kết nối MQTT hay cơ sở dữ liệu trực tiếp.

### 2. Luồng hội thoại của AI Agent


![Sơ đồ luồng AI Agent](<image/Luồng AI Agent.png>)

Agent dùng các tool backend như `get_current_pm25`, `get_station_history`, `get_pm25_forecast`, `get_active_alerts`, `get_weather_context`, `get_user_profile` và `create_warning_proposal`. Nếu tool lỗi, dữ liệu stale/invalid hoặc không có đủ evidence, Agent phải nêu rõ không đủ dữ liệu thay vì suy đoán.

## Luồng cảnh báo và Human-in-the-Loop

1. Backend Rule Engine phát hiện chỉ số vượt ngưỡng trên dữ liệu mới và hợp lệ.
2. Automatic Proposal Service gọi Agent để tổng hợp evidence và chỉ tạo warning proposal `pending` khi chính sách cho phép (có thể giới hạn theo trạm, ví dụ S05 cho demo).
3. Mỗi trạm chỉ có một proposal đang chờ; proposal quá thời hạn được chuyển sang `expired` nhưng vẫn giữ trong audit.
4. Manager mở trang Phê duyệt, xem evidence, rồi approve hoặc reject.
5. Backend ghi audit append-only. Chỉ sau approve, backend mới có thể publish command MQTT tới Device Simulator; Agent không có đường gửi command trực tiếp.



![Sơ đồ luồng cảnh báo và phê duyệt](<image/Luồng cảnh báo và phê duyệt.png>)

## Thành phần và trách nhiệm

| Thành phần | Trách nhiệm | Không được làm |
|---|---|---|
| React Dashboard | Hiển thị dữ liệu API, chat, approval và audit | Kết nối MQTT/DB trực tiếp hoặc tự suy luận alert |
| FastAPI Backend | API, AQI/alert rules, RBAC, forecast, approval và audit | Cấp quyền DB cho frontend/Agent |
| MQTT Consumer | Validate và persist dữ liệu simulator | Tạo recommendation hoặc tự approve |
| AI Agent LangGraph | Tool calling, giải thích grounded, đề xuất pending | Bịa số liệu, truy cập DB/MQTT trực tiếp, approve/reject |
| PostgreSQL | System of record: stations, measurements, alerts, proposals, audit | Cung cấp API trực tiếp cho client |
| Mosquitto MQTT | Vận chuyển measurement/status/command | Áp dụng business rule |
| Device Simulator | Nhận command đã duyệt và gửi trạng thái mô phỏng | Điều khiển thiết bị thật |

## Dữ liệu và tích hợp ngoài

- **PostgreSQL** là system of record; không có Vector Store/RAG trong MVP hiện tại.
- **OpenAI API** là tích hợp tùy chọn để diễn giải câu trả lời. Khi không có API key hoặc LLM lỗi, Agent dùng deterministic grounded composer, không bịa dữ liệu.
- **RabbitMQ, Redis và Celery** chỉ chạy với profile `async-jobs` cho tác vụ nền; không phải điều kiện để pipeline MQTT cốt lõi hoạt động.

## Bảo mật và ranh giới tin cậy

- Secret nằm trong `.env`, không commit vào repository.
- Backend validate input bằng Pydantic và là cổng duy nhất vào dữ liệu nghiệp vụ.
- Data quality (invalid, stale, offline) là gate trước khi hiển thị current value, tạo alert, forecast hoặc proposal.
- Audit ghi lại proposal create/approve/reject/expire và command dispatch/failure để truy vết.
- HITL là bắt buộc: Manager là chủ thể duy nhất được approve/reject proposal.
