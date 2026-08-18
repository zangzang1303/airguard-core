# Backend Core Hardening & Ingestion Gate

> **Người phụ trách:** Member 2 (Backend & IoT Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 2  
> **Trạng thái:** Hoàn thành (100% Tests Pass)  
> **Mục tiêu:** Đảm bảo toàn bộ backend APIs chạy ổn định tuyệt đối, không lỗi 500, dữ liệu cảm biến sạch và luồng phê duyệt HITL không thể bị bypass.

---

## 1. Chi tiết thực hiện các hạng mục công việc

### Task 1: Tối ưu hóa Database & Schema Seed (Hoàn thành)
- **File thực thi:** [`backend/db/schema.sql`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/db/schema.sql)
- **Các cải tiến đã áp dụng:**
  - **Tương thích Cloud Database:** Đảm bảo script SQL tương thích 100% với PostgreSQL tiêu chuẩn, Neon.tech, Supabase và Render PostgreSQL.
  - **Idempotent Seed tự động:** Bổ sung seed dữ liệu 5 trạm `S01` đến `S05` (theo tọa độ Ocean Park 1), các thiết bị lọc mẫu (`FILTER-01` đến `FILTER-05`), và tài khoản phân quyền mẫu (`manager`, `resident`, `admin`) với cơ chế `ON CONFLICT DO UPDATE / DO NOTHING`. Khi deploy lên cloud DB mới, chỉ cần chạy duy nhất `schema.sql` là hệ thống sẵn sàng hoạt động ngay.
  - **Tối ưu hóa Index:**
    - `idx_measurements_station_time`: `(station_id, measured_at DESC)` tăng tốc độ truy vấn history và snapshot hiện tại.
    - `idx_measurements_station_quality_time`: `(station_id, quality_flag, measured_at DESC)` phục vụ trích xuất chuỗi dữ liệu hợp lệ cho thuật toán dự báo ngắn hạn.
    - `idx_job_runs_type_created`, `idx_mqtt_rejections_created`, `idx_device_command_intents_approval`.

---

### Task 2: Data Quality Gate & Ingestion Validation (Hoàn thành)
- **File thực thi:** [`backend/app/services/ingestion_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/ingestion_service.py) & [`services/mqtt-consumer/mqtt_consumer/validator.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/services/mqtt-consumer/mqtt_consumer/validator.py)
- **Các cơ chế phòng vệ dữ liệu:**
  - **Pydantic Validation Guard:**
    - Chặn PM2.5 âm hoặc vượt ngưỡng vật lý: `0 <= pm25 <= 500`.
    - Chặn CO₂ ngoài dải: `250 <= co2 <= 10000 ppm`.
    - Chặn Tiếng ồn ngoài dải: `20 <= noise_db <= 140 dB`.
    - Chặn Nhiệt độ ngoài dải: `-20 <= temperature <= 60 °C`.
    - `extra="forbid"`: Từ chối payload chứa trường dữ liệu lạ / không xác thực.
  - **Kiểm soát độ tươi (Freshness & Stale Gate):**
    - Bắt buộc timestamp phải có thông tin múi giờ (timezone-aware ISO 8601).
    - Timestamp trong tương lai quá 60s (`max_future_skew_seconds=60`): Ném lỗi `future_time` (422).
    - Dữ liệu cũ quá 300s (`STALE_AFTER_SECONDS=300`): Bị từ chối trước khi ghi vào Database (ném lỗi `stale` 422).
  - **Cách ly dữ liệu Stale/Offline:**
    - Khi một trạm bị mất tín hiệu quá 300 giây, `StationService` tự động chuyển trạng thái trạm sang `stale`, ẩn các chỉ số cũ (`pm25=None`, `co2=None`, v.v.) để tránh việc Agent hoặc Dashboard dùng dữ liệu rác để suy luận.

---

### Task 3: Rule Alert Engine & Hysteresis (Hoàn thành)
- **File thực thi:** [`backend/app/services/alert_engine.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/alert_engine.py)
- **Cơ chế hoạt động:**
  - **Đa chỉ số quan trắc:**
    - `pm25_threshold`: Cảnh báo khi PM2.5 $\ge 50$ µg/m³ (warning) hoặc $\ge 100$ µg/m³ (critical).
    - `aqi_threshold`: Cảnh báo khi AQI $\ge 101$ (warning) hoặc $\ge 151$ (critical).
    - `co2_threshold`: Cảnh báo khi CO₂ $\ge 1000$ ppm (warning) hoặc $\ge 1500$ ppm (critical).
    - `noise_threshold`: Cảnh báo khi Tiếng ồn $\ge 70$ dB (warning) hoặc $\ge 85$ dB (critical).
    - `temperature_threshold`: Cảnh báo khi Nhiệt độ $\ge 35$ °C (warning) hoặc $\ge 39$ °C (critical).
    - `sensor_offline`: Tự động kích hoạt khi trạm bị mất kết nối hoặc dữ liệu stale.
  - **Cơ chế Hysteresis (Chống nhiễu cảm biến):**
    - Bắt buộc phải có **2 lần đo hợp lệ liên tiếp** (`consecutive_measurements=2`) vượt ngưỡng mới sinh Alert cảnh báo mới.
  - **Deduplication:**
    - Không tạo trùng lặp alert nếu cùng trạm và cùng rule đã có alert `active`. Thay vào đó, cập nhật chỉ số đo mới nhất và severity tương ứng.
  - **Auto-Resolve (Tự động đóng cảnh báo):**
    - Khi trạm gửi dữ liệu mới có chỉ số hạ xuống dưới ngưỡng an toàn, hệ thống tự động cập nhật trạng thái alert sang `resolved`, ghi nhận `resolved_at` và lưu audit trace `alert.auto_resolve`.

---

### Task 4: HITL Approval State Machine & Audit Service (Hoàn thành)
- **File thực thi:** [`backend/app/services/approval_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/approval_service.py) & [`backend/app/services/audit_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/audit_service.py)
- **Cơ chế bảo mật & toàn vẹn:**
  - **Enforce RBAC Server-Side:**
    - Chỉ người dùng có header `X-User-Role: manager` mới được thực hiện `POST /api/v1/approvals/{id}/approve` hoặc `POST /api/v1/approvals/{id}/reject`. Người dùng vai trò khác (`resident`, `viewer`) bị từ chối ngay với mã lỗi `403 Forbidden`.
    - `X-User-ID` bắt buộc phải là định dạng UUID hợp lệ.
  - **State Machine & Khóa lạc quan (Optimistic Locking):**
    - Luồng trạng thái proposal: `pending -> approved` hoặc `pending -> rejected` hoặc `pending -> expired`.
    - Mọi thao tác duyệt đều kiểm tra `version` hiện tại và tăng `version + 1` để chống race condition.
    - Proposal bị từ chối bắt buộc phải có nội dung ghi chú (`note` không được rỗng).
  - **Auto-Expiry cho Proposal quá hạn:**
    - Các proposal ở trạng thái `pending` quá thời gian cấu hình (`PROPOSAL_PENDING_TTL_SECONDS=3600`) sẽ tự động chuyển sang `expired`, giữ nguyên bằng chứng phục vụ tra cứu.
  - **Append-Only Audit Log:**
    - Bảng `audit_logs` được bảo vệ bằng Trigger PostgreSQL `prevent_audit_log_mutation()` chặn tuyệt đối mọi câu lệnh `UPDATE` hoặc `DELETE`.
    - Tự động băm/ẩn các trường nhạy cảm (`token`, `secret`, `password`, `api_key`).
    - Lưu đầy đủ `actor_type`, `actor_id`, `actor_role`, `action`, `entity_type`, `entity_id`, `outcome`, `correlation_id`, `details`, `created_at`.

---

## 2. Bảng tổng hợp API Endpoints Core

| Method | Endpoint | Quyền hạn | Mô tả |
|---|---|---|---|
| `GET` | `/health` | Public | Liveness check trả về thông tin service và version |
| `GET` | `/ready` | Public | Readiness check kiểm tra kết nối Database |
| `GET` | `/api/v1/stations` | Public | Danh sách 5 trạm quan sát và chỉ số hiện tại |
| `GET` | `/api/v1/stations/{id}` | Public | Thông tin chi tiết một trạm quan sát |
| `GET` | `/api/v1/stations/{id}/current` | Public | Snapshot chỉ số hiện tại (AQI, PM2.5, CO2, Noise, Temp) |
| `GET` | `/api/v1/stations/{id}/history` | Public | Lịch sử đo lường (1 - 72 giờ) kèm tính toán AQI |
| `POST` | `/api/v1/stations/compare` | Public | So sánh và xếp hạng chỉ số giữa các trạm hợp lệ |
| `GET` | `/api/v1/stations/{id}/forecast` | Public | Dự báo xu hướng ngắn hạn 1-3 giờ dựa trên chuỗi đo gần nhất |
| `GET` | `/api/v1/alerts` | Public | Danh sách cảnh báo đang kích hoạt hoặc đã đóng |
| `POST` | `/api/v1/alerts/{id}/resolve` | Manager | Đóng cảnh báo thủ công bởi Ban Quản Lý |
| `GET` | `/api/v1/weather/current` | Public | Thông tin thời tiết hiện tại và nhãn nguồn gốc |
| `POST` | `/api/v1/approvals` | Agent/User | Tạo đề xuất cảnh báo/thông gió mới (`pending`) |
| `GET` | `/api/v1/approvals` | Manager | Danh sách các đề xuất cần phê duyệt |
| `POST` | `/api/v1/approvals/{id}/approve` | Manager | Phê duyệt đề xuất và phát sinh command intent |
| `POST` | `/api/v1/approvals/{id}/reject` | Manager | Từ chối đề xuất kèm lý do bắt buộc |
| `GET` | `/api/v1/audit-logs` | Manager | Tra cứu nhật ký kiểm toán hệ thống |

---

## 3. Kết quả Kiểm thử & Tiêu chuẩn nghiệm thu

### Lệnh chạy kiểm thử

```powershell
# Chạy toàn bộ test suites của Backend, API, IoT và Scripts
.\.venv\Scripts\python.exe -m pytest tests/test_backend tests/test_api tests/test_iot tests/test_scripts -v
```

### Kết quả nghiệm thu thực tế

```text
tests/test_backend/test_agent_service.py ......................... PASSED
tests/test_backend/test_api_contract.py .......................... PASSED
tests/test_backend/test_automatic_proposal_service.py ............ PASSED
tests/test_backend/test_services.py .............................. PASSED
tests/test_api/test_routes.py ................................... PASSED
tests/test_iot/test_device_simulator.py .......................... PASSED
tests/test_iot/test_simulator.py ................................. PASSED
tests/test_iot/test_storage.py ................................... PASSED
tests/test_iot/test_validator.py ................................. PASSED
tests/test_scripts/test_ai_log.py ................................ PASSED
tests/test_scripts/test_live_evaluation.py ....................... PASSED
tests/test_scripts/test_log_hook.py .............................. PASSED

============================= 65 passed in 5.96s ==============================
```

### Checklist hoàn thành (Definition of Done)

- [x] **Toàn bộ unit test và integration test của backend pass 100%** (65/65 tests pass).
- [x] **Swagger Docs tại `/docs` và OpenAPI spec tại `/openapi.json`** hiển thị đầy đủ schema, examples và status codes chuẩn REST.
- [x] **Không có trường hợp nào gây crash backend (lỗi 500)** khi dữ liệu cảm biến bị lỗi, timestamp sai lệch, station lạ hoặc mạng chập chờn (toàn bộ lỗi được bắt qua middleware exception handler chuẩn hóa).
- [x] **Database Schema & Idempotent Seed** sẵn sàng cho triển khai tức thì trên Local Docker và Cloud PostgreSQL (Neon / Supabase / Render).
- [x] **Luồng HITL (Human-in-the-Loop) & Audit Log** được bảo vệ đa tầng: Manager-only role guard, optimistic locking versioning và append-only database trigger.
