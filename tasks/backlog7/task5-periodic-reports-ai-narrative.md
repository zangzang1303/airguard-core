# Task B7-05: Báo Cáo Môi Trường Chuẩn ESG, Ma Trận 7x24h & AI Narrative Xuất Bản

> **Người phụ trách:** Backend Analytics Engineer & AI Narrative Specialist  
> **Thời hạn dự kiến:** Ngày 3  
> **Mục tiêu:** 
> 1. Xây dựng dịch vụ báo cáo môi trường tự động (Daily 00:10, Weekly 00:20 Thứ Hai) theo định hướng **Báo cáo ESG Đô Thị Thông Minh & Hiệu Quả Năng Lượng**.
> 2. Tính toán các chỉ số thực tế: Khối lượng bụi mịn đã thanh lọc ($kg$), Số kWh điện tiết kiệm nhờ `eco_mode`, và Tỷ lệ tuân thủ quy chuẩn **QCVN 05:2023/BTNMT**.
> 3. Trực quan hóa **Ma Trận Diễn Biến 7 Ngày x 24 Giờ (Weekly 7x24 Diurnal Heat Matrix)**.
> 4. Xuất bản tài liệu PDF cao cấp có nhúng biểu đồ vector, bảng thống kê và lời bình luận có kiểm định trung thực số liệu (Zero Hallucination).

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Reporting & ESG Analytics Engine
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/report_generator_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/report_generator_service.py)
  - [`backend/app/services/report_narrative_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/report_narrative_service.py)
  - [`backend/app/services/report_repository.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/report_repository.py)
  - [`backend/app/tasks/report_tasks.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/tasks/report_tasks.py)
- **Nhiệm vụ cụ thể**:
  1. **Tính toán Chỉ số Xanh & Hiệu Quả Năng Lượng (ESG Metrics)**:
     - **Khối lượng bụi mịn đã thanh lọc**:
       $$\text{PM2.5 Cleared (kg)} = \sum \Delta \text{PM2.5 } (\mu\text{g/m}^3) \times \text{Airflow Volume } (V_{\text{boost}} \text{ m}^3) \times 10^{-9}$$
     - **Điện năng tiết kiệm nhờ chuyển kịp thời sang `eco_mode`**:
       $$\text{Energy Saved (kWh)} = \Delta P_{\text{boost - eco}} (\text{kW}) \times \text{Hours in Eco Mode}$$
     - *Giá trị thực tế*: Giúp Ban Quản Lý chứng minh hiệu quả đầu tư hệ thống lọc khí và tiết kiệm chi phí vận hành tòa nhà.
  2. **Đánh giá Tuân Thủ Quy Chuẩn Quốc Gia QCVN 05:2023/BTNMT**:
     - So sánh giá trị trung bình 24h của PM2.5 với ngưỡng quy chuẩn Việt Nam ($50\text{ µg/m³}$) và khuyến cáo WHO ($15\text{ µg/m³}$).
     - Đánh giá tỷ lệ giờ trong ngày đạt tiêu chuẩn Không khí Tốt ($\ge 85\%$).
  3. **AI Narrative Engine với Grounding Gate Tuyệt Đối**:
     - Prompt mẫu yêu cầu LLM viết văn phong trang trọng, có mở đầu, phân tích nguyên nhân (thời tiết, giao thông), đánh giá hiệu quả can thiệp của BQL và khuyến nghị tuần tới.
     - **Grounding Gate**: Bắt buộc mọi con số thống kê (AQI max, PM2.5 trung bình, giờ cao điểm, điện năng) phải khớp 100% với database; nếu phát hiện số sai lệch $\rightarrow$ Fallback sang bộ soạn thảo chuẩn xác định (Deterministic Composer).

---

### 1.2. Frontend Reports Hub & Xuất PDF Xuất Bản
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/admin/ReportsDrawer.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/admin/)
  - [`frontend/src/features/admin/WeeklyMatrixChart.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/admin/) *(Component mới)*
- **Nhiệm vụ cụ thể**:
  1. **Biểu đồ Ma Trận Nhiệt 7 Ngày x 24 Giờ**:
     - Trực quan hóa bảng lưới $7 \times 24$ ô màu: Giúp BQL nhìn vào thấy ngay quy luật ô nhiễm (VD: Sáng thứ Hai từ 7–9h luôn có màu Đỏ do lượng xe đi làm cao, Chiều Chủ Nhật ven Hồ Ngọc Trai có màu Xanh mát).
  2. **Bộ Xuất Báo Cáo PDF Chuẩn A4 Đẹp Mắt**:
     - Sử dụng HTML Template in ấn chuyên nghiệp (Header logo, watermark, bảng màu phân cấp, biểu đồ tóm tắt).
     - Hỗ trợ tải về 3 định dạng: **PDF (.pdf)** cho báo cáo in ấn, **HTML (.html)** cho xem web, và **Markdown (.md)** cho tích hợp tài liệu nội bộ.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_report_generator.py -v
```

### 2.2. Test xuất file và kiểm tra độ chính xác (Verification Test)
- [ ] Kích hoạt tạo Báo cáo Tuần qua API:
  ```powershell
  Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/reports/generate" -ContentType "application/json" -Body '{"report_type": "weekly"}'
  ```
- [ ] Tải file PDF từ endpoint `/api/v1/reports/{id}/export?format=pdf`:
  - Mở file kiểm tra: Có đủ số liệu 5 trạm, chỉ số bụi đã lọc ($kg$), điện năng tiết kiệm ($kWh$) và đoạn nhận xét sắc sảo của AI.
  - Kiểm tra đối chiếu: Mọi con số trong bài viết của AI trùng khớp 100% với bảng phụ lục thống kê.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ 100% báo cáo tạo ra không có hiện tượng bịa đặt số liệu (Zero Hallucination).
2. ✅ File PDF có thiết kế thẩm mỹ cao, căn lề chuẩn trang A4 và đầy đủ biểu đồ.
3. ✅ Báo cáo tích hợp đầy đủ các chỉ số ESG và đối sánh quy chuẩn QCVN 05:2023/BTNMT.
