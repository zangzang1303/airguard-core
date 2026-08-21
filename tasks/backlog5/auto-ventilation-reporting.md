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
  [Khi chỉ số giảm an toàn 20 phút -> Tự động đưa về Eco & Audit đóng chu trình]
```

### 1.2. API & Database Schema
* Bổ sung trường `device_id`, `action_type` (`ventilation_boost`, `air_purifier_on`, `eco_mode`), `duration_minutes` trong bảng `warning_proposals`.
* Endpoint Duyệt nhanh 1 chạm: `POST /api/v1/approvals/{id}/quick-approve`.

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

- [ ] Khi simulator phát kịch bản `spike`, hệ thống tự động sinh Proposal thông gió mà không cần thao tác gõ lệnh thủ công.
- [ ] BQL bấm Duyệt 1 chạm $\rightarrow$ Device Simulator nhận command trong $< 1$ giây $\rightarrow$ Trạng thái thiết bị đổi sang `RUNNING_BOOST`.
- [ ] Báo cáo môi trường định kỳ được sinh tự động, số liệu thống kê khớp 100% với dữ liệu database, lời bình của AI khách quan, mạch lạc.
