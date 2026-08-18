# Backend Core Hardening & Ingestion Gate

> **Người phụ trách:** Member 2 (Backend & IoT Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 2  
> **Mục tiêu:** Đảm bảo toàn bộ backend APIs chạy ổn định tuyệt đối, không lỗi 500, dữ liệu cảm biến sạch và luồng phê duyệt HITL không thể bị bypass.

---

## 1. Các hạng mục công việc cần hoàn thành

### Task 1: Tối ưu hóa Database & Schema Seed
- File: [`backend/db/schema.sql`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/db/schema.sql)
- Đảm bảo script SQL chạy được trên cả PostgreSQL local và Cloud Database (Neon / Supabase / Render Postgres).
- Tự động seed 5 trạm `S01` đến `S05` nếu chưa tồn tại (idempotent seed).
- Đảm bảo index `(station_id, measured_at DESC)` để tăng tốc độ query history và current value.

### Task 2: Data Quality Gate & Ingestion Validation
- File: [`backend/app/services/ingestion_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/ingestion_service.py) & [`services/mqtt-consumer/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/services/mqtt-consumer/mqtt_consumer/validator.py)
- Chặn mọi payload không hợp lệ: PM2.5 âm, timestamp tương lai quá 60s, thiếu trường bắt buộc, hoặc station_id lạ.
- Gắn nhãn `is_stale=True` nếu trạm không gửi dữ liệu quá 300 giây (`STALE_AFTER_SECONDS`).
- Không cho phép dữ liệu stale/invalid kích hoạt cảnh báo mới hoặc làm sai lệch kết quả của Agent.

### Task 3: Rule Alert Engine & Hysteresis
- File: [`backend/app/services/alert_engine.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/alert_engine.py)
- Đảm bảo cơ chế cảnh báo đa chỉ số (PM2.5, AQI, CO₂, Tiếng ồn, Nhiệt độ, Sensor Offline) hoạt động chuẩn xác:
  - Cần **2 lần đo liên tiếp** vượt ngưỡng mới sinh Alert (tránh nhiễu đột biến cảm biến).
  - Deduplicate: Không sinh nhiều alert trùng lặp cho cùng 1 trạm/rule đang active.
  - Auto-resolve: Tự động đánh dấu `resolved` khi chỉ số hạ xuống dưới ngưỡng an toàn liên tục.

### Task 4: HITL Approval State Machine & Audit Service
- File: [`backend/app/services/approval_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/approval_service.py) & [`backend/app/services/audit_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/audit_service.py)
- Enforce quyền Manager trên backend: Chỉ `role=manager` mới được gọi `POST /api/v1/approvals/{id}/approve` hoặc `reject`.
- Ghi log Append-Only vào bảng `audit_logs` với đầy đủ: `actor`, `action`, `target_id`, `outcome`, `correlation_id`, `timestamp`.

---

## 2. Kiểm thử & Tiêu chuẩn nghiệm thu

```powershell
# Chạy bộ test backend
.\.venv\Scripts\python.exe -m pytest tests/test_backend tests/test_api -v
```

- [ ] Toàn bộ unit test và integration test của backend pass 100%.
- [ ] Swagger Docs tại `/docs` hiển thị đầy đủ schema và mô tả rõ ràng.
- [ ] Không có trường hợp nào gây crash backend khi dữ liệu cảm biến bị lỗi hoặc mạng chập chờn.
