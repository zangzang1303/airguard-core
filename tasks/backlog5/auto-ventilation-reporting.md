# Tự động Điều tiết Thông gió & Báo cáo Môi trường Định kỳ

> **Người phụ trách:** Member 2 (Backend) + Member 3 (AI Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 5  
> **Mục tiêu:** Xây dựng luồng tự động hóa đề xuất điều tiết hệ thống thông gió tòa nhà khi có ô nhiễm và Động cơ xuất báo cáo định kỳ (Daily/Weekly Digest) tự động bằng LLM.

---

## 1. Tự động Điều tiết Thông gió (Auto Ventilation Dispatching Loop)

### 1.1. Logic Kích hoạt Tự động
```text
Cảm biến CO2 > 1000 ppm HOẶC PM2.5 > 50 µg/m³ kéo dài > 15 phút
                                │
                                ▼
         [Agent Auto-Assessment: Đánh giá đợt ô nhiễm]
                                │
                                ▼
  [Tạo Warning Proposal Pending: Đề xuất bật quạt thông gió 80% trong 45 phút]
                                │
                                ▼
               [Thông báo Push / Email tới Ban Quản Lý]
                                │
                                ▼
            [BQL Duyệt 1 chạm (Quick Approve / Cooldown)]
                                │
                                ▼
        [Backend Publish Command -> Device Simulator ghi nhận]
                                │
                                ▼
 [Khi chỉ số giảm an toàn 20 phút -> Tạo Eco Proposal Pending -> BQL duyệt -> Dispatch & Audit]
```

### 1.2. API & Database Schema
* Tiếp tục dùng `approval_requests` làm system of record và bổ sung tương thích các field `device_id`, canonical `proposed_action` (`ventilation_boost`, `air_purifier_on`, `eco_mode`), `duration_minutes`, `intensity_percent`; không tạo bảng proposal thứ hai.
* Endpoint Duyệt nhanh 1 chạm: `POST /api/v1/approvals/{id}/quick-approve`.
* Proposal mới được gửi vào notification job idempotent cho các tài khoản Manager/Admin đang hoạt động. SMTP là tùy chọn; chế độ local `disabled` ghi trạng thái `not_configured` minh bạch và không làm mất proposal.

---

## 2. Động cơ Báo cáo Môi trường Định kỳ (Environmental Digest Engine)

### 2.1. Kiến trúc Báo cáo
* **Daily Digest (Hàng ngày)**:
  - Tóm tắt AQI trung bình, điểm ô nhiễm nhất trong ngày, số lần vượt ngưỡng.
  - Tổng thời gian hệ thống lọc khí / thông gió đã được kích hoạt.
  - LLM viết đoạn văn nhận xét tổng quan 3–5 câu ngắn gọn.
* **Weekly Report (Hàng tuần)**:
  - Phân tích xu hướng ô nhiễm theo các ngày trong tuần (so sánh thứ Hai với cuối tuần).
  - Đánh giá hiệu quả giảm thiểu ô nhiễm sau khi bật thông gió.
  - Khuyến nghị bảo trì cảm biến / vệ sinh màng lọc định kỳ.

### 2.2. Triển khai Service
* Tạo file: `backend/app/services/report_generator_service.py`.
* API Endpoints:
  - `GET /api/v1/reports?type=daily|weekly` — Lấy danh sách báo cáo đã sinh.
  - `GET /api/v1/reports/{id}` — Xem chi tiết báo cáo (hỗ trợ render HTML/Markdown & xuất PDF).
  - `POST /api/v1/reports/generate` — BQL có thể bấm nút tạo báo cáo tức thời cho khoảng thời gian tùy chọn.

---

## 3. Tiêu chuẩn nghiệm thu

- [x] Integration tests xác minh Rule Engine chỉ cho qua sau 15 phút liên tục và chặn stale/offline/invalid/gap; live Agent smoke trả `generation_mode=live_llm` với grounded source; orchestration test xác minh chỉ tạo đúng một proposal thông gió `pending`.
- [x] BQL bấm Duyệt 1 chạm $\rightarrow$ Device Simulator nhận command trong $< 1$ giây $\rightarrow$ trạng thái đổi sang `RUNNING_BOOST`. Full-stack ngày 22/08/2026: API trả sau 107 ms, ACK quan sát sau 129 ms và timestamp DB ghi approve $\rightarrow$ ACK 72.120 ms; luồng dùng Manager session, CSRF, version và idempotency thật.
- [x] Báo cáo daily/weekly được Celery Beat lập lịch, aggregation khớp fixture DB trong test, export Markdown/HTML/PDF dùng cùng record và LLM lỗi có deterministic grounded fallback.
- [x] Proposal pending enqueue đúng một notification job cho mỗi Manager/Admin; audit không ghi email và lỗi notification không làm thay đổi trạng thái HITL.

## 4. Trạng thái triển khai Person B — 22/08/2026

- `approval_requests` vẫn là system of record; migration chỉ thêm field/lifecycle và không tạo bảng proposal thứ hai.
- Backend tự map S03 sang `FILTER-01`; action allow-list là `ventilation_boost`, `air_purifier_on`, `eco_mode`.
- `eco_mode` sau 20 phút an toàn chỉ được tạo ở trạng thái `pending`; không bypass Manager HITL theo ADR 0011.
- ACK được correlate bằng stable `command_id`, lưu event/audit và không cho ACK unmatched/out-of-order đổi device truth.
- MQTT dispatcher disconnect trước khi join network loop sau QoS publish; quick-approve không còn chờ thêm khoảng một giây trong eager-mode/full-stack local.
- Report lưu type/range/timezone/status/statistics/evidence/narrative/mode/source; retry failed hoặc lease stale dùng cùng report record.
- Test phạm vi nằm tại `test_auto_ventilation.py`, `test_quick_approval.py`, `test_report_generator.py`, `test_person_b_api_security.py` và IoT storage/device tests.
- Quality gate tích hợp: `289 passed`; Ruff toàn bộ backend services/tasks/test_backend pass; frontend production build pass. Celery worker/Beat chạy non-root; weekly report task qua RabbitMQ/Redis và notification task đều `SUCCESS`.
