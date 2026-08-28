# Task B7-05: Báo Cáo Môi Trường Định Kỳ & AI Narrative

> **Người phụ trách:** Backend Engineer & AI Specialist  
> **Thời hạn dự kiến:** Ngày 3  
> **Mục tiêu:** Hoàn thiện dịch vụ tự động lập Báo cáo Môi trường Ngày (Daily lúc 00:10) và Tuần (Weekly lúc 00:20 thứ Hai) qua Celery Beat, sử dụng LLM để tạo lời bình luận (Narrative) có kiểm soát chống ảo giác số liệu, và hỗ trợ xuất báo cáo đa định dạng (Markdown, HTML, PDF có biểu đồ).

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Reporting Engine & Celery Beat
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/report_generator_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/report_generator_service.py)
  - [`backend/app/services/report_narrative_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/report_narrative_service.py)
  - [`backend/app/services/report_repository.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/report_repository.py)
  - [`backend/app/tasks/report_tasks.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/tasks/report_tasks.py)
- **Nhiệm vụ cụ thể**:
  1. **Lập lịch Celery Beat chuẩn UTC+7**:
     - `generate_daily_report`: Chạy lúc `00:10` hằng ngày cho chu kỳ 24h ngày hôm trước (`00:00:00 - 23:59:59`).
     - `generate_weekly_report`: Chạy lúc `00:20` thứ Hai hằng tuần cho chu kỳ 7 ngày tuần trước.
     - Khóa phân tán chống trùng lặp theo `(report_type, period_start, period_end, timezone)`.
  2. **Tổng hợp Thống kê Toán học**:
     - Tính AQI mean/max, PM2.5 mean/max, CO2 mean/max, Noise mean/max cho từng trạm và toàn khu đô thị.
     - Thống kê tổng số đợt cảnh báo theo mức độ nghiêm trọng và số lần quạt thông gió được kích hoạt.
  3. **AI Narrative Engine có Grounding Validator**:
     - Gửi prompt yêu cầu LLM viết bản nhận xét tình hình môi trường, so sánh với quy chuẩn QCVN 05:2023/BTNMT.
     - **Validator**: Kiểm tra tất cả các con số xuất hiện trong đoạn văn của LLM phải khớp 100% với số liệu trong `statistics_json`. Nếu phát hiện số lạ $\rightarrow$ Tự động hủy và dùng Deterministic Template để đảm bảo Zero Hallucination.
  4. **Xuất file Đa định dạng (Exporter)**:
     - Xuất file Markdown (`.md`), HTML giao diện in ấn đẹp (`.html`), và PDF (`.pdf`).

### 1.2. Frontend Reports Viewer & Download
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/admin/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/admin/) (Giao diện Quản lý Báo cáo)
- **Nhiệm vụ cụ thể**:
  1. **Danh sách Báo cáo Định kỳ**: Hiển thị bảng danh sách các báo cáo Ngày và Tuần kèm bộ lọc thời gian.
  2. **Trình xem trước Báo cáo (Report Modal)**: Xem trực tiếp nội dung nhận xét của AI, bảng số liệu 5 trạm và biểu đồ tương tác.
  3. **Nút Tải về 1-Click**: Tải file PDF, HTML hoặc Markdown ngay trên giao diện.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_report_generator.py -v
```

### 2.2. Test API & Xuất File (Manual Test)
1. **Gọi API tạo báo cáo thủ công**:
   ```powershell
   Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/reports/generate" -ContentType "application/json" -Body '{"report_type": "daily"}'
   ```
2. **Kiểm tra file tải về**:
   - Gọi `GET /api/v1/reports/{report_id}/export?format=pdf`.
   - Mở file PDF: Kiểm tra tiêu đề *"BÁO CÁO CHẤT LƯỢNG MÔI TRƯỜNG VINHOMES OCEAN PARK 1"*, bảng số liệu 5 trạm đầy đủ, căn lề trang A4 chuẩn xác.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ 100% số liệu trong bài viết Narrative của AI khớp chính xác với bảng thống kê.
2. ✅ File PDF xuất ra có layout chuyên nghiệp, hiển thị đúng font tiếng Việt UTF-8.
3. ✅ Celery Beat tạo đúng giờ và không tạo trùng lặp báo cáo.
