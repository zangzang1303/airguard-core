# Task B7-02: Cảnh Báo Cá Nhân Hóa 3 Nhóm Sức Khỏe & Gửi Email

> **Người phụ trách:** Backend Engineer & AI Agent Lead  
> **Thời hạn dự kiến:** Ngày 2  
> **Mục tiêu:** Hoàn thiện cơ chế phân loại cảnh báo thông minh theo 3 nhóm đối tượng (`sensitive`, `normal`, `outdoor_sport`), tích hợp gửi Email qua Resend API có cơ chế chống spam (Debounce & Cooldown), và tối ưu khả năng trả lời tư vấn của AI Agent.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Core & Notification Service
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/resident_alert_notification_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/resident_alert_notification_service.py)
  - [`backend/app/services/environmental_scoring.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/environmental_scoring.py)
  - [`backend/app/services/resend_email_provider.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/resend_email_provider.py)
  - [`backend/app/services/email_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/email_service.py)
- **Nhiệm vụ cụ thể**:
  1. **Quy tắc phân tầng cảnh báo sớm (Early Warning Thresholds)**:
     - Nhóm `sensitive`: Kích hoạt cảnh báo cấp độ Vàng khi PM2.5 vượt $35.5\text{ µg/m³}$ hoặc AQI $> 50$ kèm khuyến nghị đóng cửa sổ và bật máy lọc không khí.
     - Nhóm `outdoor_sport`: Kích hoạt cảnh báo khi PM2.5 vượt $55.4\text{ µg/m³}$ hoặc AQI $> 100$ kèm gợi ý chuyển sang tập thể dục trong nhà hoặc tìm trạm sạch nhất.
     - Nhóm `normal`: Cảnh báo khi vượt ngưỡng Cam/Đỏ (AQI $> 150$).
  2. **Bộ lọc chống mệt mỏi cảnh báo (Alert Fatigue Filter)**:
     - **Debounce**: Bắt buộc phát hiện vượt ngưỡng trong ít nhất 2 chu kỳ đo liên tiếp ($20\text{s}$).
     - **Cooldown**: Khóa gửi lại email cho cùng 1 user và 1 trạm trong vòng $60\text{ phút}$, trừ khi mức độ nghiêm trọng leo thang từ `warning` lên `danger`.
     - **Idempotency Key**: Sinh khóa `uuid5(alert_id, user_id, severity)` chống gửi trùng lặp.
  3. **Template Email HTML Resend**: Thiết kế mẫu Email HTML responsive, hiển thị rõ chỉ số ô nhiễm, trạm ghi nhận, biểu tượng cảnh báo màu sắc và lời khuyên hành động tức thời.

### 1.2. Frontend UI / UX & Profile Drawer
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/profile/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/profile/) (Drawer cài đặt hồ sơ sức khỏe)
  - [`frontend/src/features/alerts/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/alerts/) (Alert Banners & Drawer)
  - [`frontend/src/features/agent/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/agent/) (Chatbot widget)
- **Nhiệm vụ cụ thể**:
  1. **User Profile Selector**: Cho phép cư dân chọn 1 trong 3 nhóm sức khỏe trong Profile Drawer kèm mô tả rõ ràng.
  2. **Banner Cảnh báo Động**: Hiển thị Banner trên đầu trang dashboard với màu sắc tương ứng mức cảnh báo của nhóm người dùng đang chọn.
  3. **Tương tác Chatbot AI**: Khi cư dân hỏi câu hỏi tự nhiên (*"Tôi bị hen suyễn thì giờ có nên ra hồ Ngọc Trai đi dạo không?"*), AI Agent tự động đọc profile `sensitive` và dữ liệu thời gian thực của trạm S03 để đưa ra câu trả lời có căn cứ khoa học.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
Chạy lệnh kiểm thử notification và agent recommendation:
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_notification_tasks_resend.py tests/test_agents/test_recommendations.py -v
```

### 2.2. Test thủ công trên Giao diện (Manual Checklist)
- [ ] Đăng nhập tài khoản cư dân: `resident1` (Nhóm `sensitive`).
- [ ] Điều khiển Simulator tạo sự cố PM2.5 tăng lên $65\text{ µg/m³}$ tại trạm S03.
- [ ] Kiểm tra trên Dashboard:
  - Banner cảnh báo màu Cam xuất hiện ngay lập tức.
  - Nội dung cảnh báo ghi rõ: *"Khuyến nghị cho nhóm nhạy cảm: Đóng cửa sổ, hạn chế ra ngoài, bật máy lọc không khí."*
- [ ] Chuyển tài khoản sang `runner_sport` (Nhóm `outdoor_sport`):
  - Mở khung chat AI, hỏi: *"Hôm nay chạy bộ ở đâu tốt nhất?"*
  - AI Agent gợi ý trạm S05 (Park River) có AQI $= 25$ kèm khung giờ tối ưu.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ 100% email thông báo được định dạng HTML chuẩn, không lỗi font tiếng Việt.
2. ✅ Không có hiện tượng spam email khi cảm biến gửi dữ liệu định kỳ mỗi 10s.
3. ✅ AI Agent trả lời đúng 100% intent cá nhân hóa trong tập kiểm thử 62 Golden Cases.
