# Task B7-02: Cảnh Báo Sớm Cá Nhân Hóa, Tính Liều Lượng Bụi & Lộ Trình Sạch

> **Người phụ trách:** Backend Engineer & AI Agent Lead  
> **Thời hạn dự kiến:** Ngày 2  
> **Mục tiêu:** 
> 1. Xây dựng cơ chế **Cảnh báo Dự báo Sớm (Predictive Early Warning)**: Báo trước 30–60 phút trước khi đợt ô nhiễm tràn tới theo mô hình dự báo.
> 2. Tính toán **Liều lượng Bụi Mịn Hít Phải (Inhaled PM2.5 Dose)** theo cường độ vận động (Nghỉ ngơi 6 L/phút vs Chạy bộ 45 L/phút).
> 3. Tích hợp **Lộ trình Chạy bộ Sạch (AQI-Aware Clean Running Route)** trên bản đồ OpenStreetMap.
> 4. Email HTML tương tác 2 chiều qua Resend API có Checklist hành động 1-Click và Deep link.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Core & Dược Động Học Hô Hấp (Inhaled Dose Engine)
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/resident_alert_notification_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/resident_alert_notification_service.py)
  - [`backend/app/services/environmental_scoring.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/environmental_scoring.py)
  - [`backend/app/services/road_graph_router.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/road_graph_router.py)
  - [`backend/app/services/resend_email_provider.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/resend_email_provider.py)
- **Nhiệm vụ cụ thể**:
  1. **Tính toán Liều Lượng Bụi Hít Phải (Inhaled Dose Calculation)**:
     $$\text{Dose } (\mu\text{g}) = \text{PM2.5 Conc } (\mu\text{g/m}^3) \times \text{Ventilation Rate } (V_E \text{ m}^3/\text{min}) \times \text{Duration } (t \text{ min})$$
     - Nhóm `normal` nghỉ ngơi trong phòng: $V_E = 0.006\text{ m}^3/\text{phút}$ (6 L/min).
     - Nhóm `outdoor_sport` chạy bộ ngoài trời: $V_E = 0.045\text{ m}^3/\text{phút}$ (45 L/min $\rightarrow$ Hít bụi gấp **7.5 lần** so với người bình thường!).
     - *Ứng dụng*: AI Agent dùng công thức này để chứng minh thuyết phục: *"Nếu bạn chạy bộ 30 phút quanh trạm S01 lúc này, phổi bạn sẽ hấp thụ $115\text{ µg}$ bụi mịn, tương đương hút 2.5 điếu thuốc lá."*
  2. **Cơ chế Cảnh Báo Dự Báo Sớm (Predictive Warning)**:
     - Không đợi đến khi PM2.5 vượt ngưỡng thực tế. Nếu mô hình dự báo chỉ ra trong $1\text{–}2\text{ giờ}$ tới trạm sẽ chạm mức Đỏ/Tím $\rightarrow$ Gửi thông báo trước **45 phút** để người dân kịp đóng cửa sổ và mang đồ phơi vào nhà.
  3. **Định Tuyến Đường Chạy Bộ Sạch Nhất (AQI-Aware Multi-objective Routing)**:
     - Thuật toán Dijkstra đa mục tiêu trên mạng lưới đường OSM Ocean Park 1: Cân bằng giữa khoảng cách (Distance) và mức độ phơi nhiễm ô nhiễm tích lũy (Cumulative Pollution Exposure).

---

### 1.2. Frontend UI & Email Tương Tác 2 Chiều
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/profile/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/profile/) (Health Profile Drawer)
  - [`frontend/src/features/alerts/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/alerts/) (Interactive Alert Cards)
  - [`frontend/src/features/map/SuperMap.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/SuperMap.tsx) (Clean Route Overlay Polyline)
- **Nhiệm vụ cụ thể**:
  1. **Hiển thị Tuyến Đường Chạy Sạch Trên Bản Đồ**:
     - Khi người dùng chọn nhóm `outdoor_sport` và hỏi đường chạy, bản đồ vẽ đường Polyline màu xanh Cyan quanh Hồ Ngọc Trai kèm thông số: Cự ly ($3.2\text{ km}$), Thời gian ($22\text{ phút}$), Lượng bụi tránh được ($68\%$).
  2. **Email HTML Tương Tác Qua Resend API**:
     - Mẫu Email sang trọng, có nút bấm:
       * `[Xem Bản Đồ Trực Tiếp]` (Mở web app và fly-to trạm tương ứng).
       * `[Checklist Hành Động]`: Danh sách việc cần làm (Đóng cửa ban công, bật máy lọc khí, đeo khẩu trang N95).
  3. **Chống Spam Thông Minh (Debounce & Smart Cooldown)**:
     - Khóa gửi email 60 phút, nhưng nếu chuyển sang mức cực kỳ nguy hại (Hazardous AQI $> 300$) ➔ Tự động phá vỡ cooldown để gửi cảnh báo khẩn cấp (Emergency Break-through).

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_notification_tasks_resend.py tests/test_agents/test_recommendations.py tests/test_agents/test_tools.py -v
```

### 2.2. Test kịch bản thực tế (Live Testing)
- [ ] Chọn profile `outdoor_sport`: Hỏi chatbot *"Tôi muốn chạy 5km, hãy chỉ đường ít bụi nhất"*.
  - AI Agent vẽ lộ trình polyline quanh hồ Ngọc Trai và khuôn viên VinUni.
  - Phản hồi giải thích rõ vì sao không nên chạy theo trục đường Đa Tốn (S01).
- [ ] Kích hoạt kịch bản dự báo ô nhiễm tăng trong 1 giờ tới:
  - Nhận thông báo sớm: *"Dự báo sau 45 phút nữa khói bụi giờ tan tầm sẽ tăng cao tại khu Sapphire, hãy đóng cửa sổ trước 17:30."*

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ Công thức Inhaled Dose tính toán chính xác theo lưu lượng thở của 3 nhóm người dùng.
2. ✅ Tuyến đường chạy bộ trên bản đồ tuân thủ 100% đồ thị đường thực tế của OpenStreetMap.
3. ✅ Email gửi qua Resend có tỷ lệ giao nhận thành công và hiển thị hoàn hảo trên cả điện thoại và máy tính.
