# Task B7-03: Bản Đồ Nhiệt Lan Truyền Khí Động Học, Hấp Thụ Mặt Nước & Hạt Gió Động

> **Người phụ trách:** Backend Spatial Engineer & Frontend WebGL / Canvas Specialist  
> **Thời hạn dự kiến:** Ngày 1 - Ngày 2  
> **Mục tiêu:** 
> 1. Hoàn thiện mô hình lan truyền khí động học **Wind-adjusted IDW** có tính toán **Hệ số Hấp thụ Mặt Nước (Water Body Absorption)** của Hồ Ngọc Trai (24.5ha) và Biển Hồ nước mặn (6.1ha).
> 2. Bổ sung **Hoạt ảnh Luồng Hạt Gió Động (Canvas Wind Particles Animation)** tương tự Windy.com.
> 3. Tính năng **"Đo Chất Lượng Tại Tòa Nhà Của Bạn" (Pick on Map)**: Bấm vào bất kỳ vị trí căn hộ nào trên bản đồ để nhận ngay báo cáo nội suy 5 chỉ số môi trường.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Spatial Engine & Địa Hình Đô Thị
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/spatial_dispersion_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/spatial_dispersion_service.py)
  - [`backend/app/services/weather_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/weather_service.py)
  - [`backend/app/main.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/main.py) (Endpoint `/api/v1/spatial/dispersion`, `/api/v1/spatial/point-assessment`)
- **Nhiệm vụ cụ thể**:
  1. **Hiệu ứng Mặt Nước Điều Hòa (Water Body Dispersion Damping)**:
     - Vinhomes Ocean Park 1 có diện tích mặt nước rất lớn: Hồ Ngọc Trai ($24.5\text{ ha}$) và Biển Hồ ($6.1\text{ ha}$).
     - Các điểm lưới nằm trên bề mặt nước hoặc trong bán kính $150\text{m}$ quanh hồ được áp dụng hệ số làm sạch tự nhiên:
       * Nồng độ PM2.5 giảm tự nhiên $15\text{–}20\%$ do hơi ẩm lắng đọng bụi.
       * Nhiệt độ giảm $1.0\text{–}2.0^\circ\text{C}$ nhờ hiệu ứng bốc hơi làm mát.
  2. **Thuật toán Khí Động Học Gió 2 Chiều (Wind-Vector IDW)**:
     $$d_{\text{effective}} = \frac{d_{\text{Euclid}}}{1.0 + 0.18 \cdot \text{wind\_speed} \cdot \cos(\theta_{\text{wind}})}$$
     - Chiều xuôi gió ($\cos\theta > 0$): Ô nhiễm lan xa hơn và nồng độ đậm hơn.
     - Chiều ngược gió ($\cos\theta < 0$): Ô nhiễm bị cản lại và pha loãng nhanh chóng.
  3. **API Đo Điểm Tùy Chọn (Point Assessment Endpoint)**:
     - Nhận tọa độ $(\text{lat}, \text{lon})$ từ người dùng $\rightarrow$ Trả về giá trị nội suy 5 chỉ số, mức độ an toàn và trạm đo gần nhất đóng vai trò tham chiếu.

---

### 1.2. Frontend UI / Canvas WebGL & Hạt Gió Động
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/stations/HeatmapLayer.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/stations/HeatmapLayer.tsx)
  - [`frontend/src/features/map/WindParticlesLayer.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/) *(Component mới)*
  - [`frontend/src/features/map/OceanParkBoundary.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/OceanParkBoundary.tsx)
  - [`frontend/src/features/map/SuperMap.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/SuperMap.tsx)
- **Nhiệm vụ cụ thể**:
  1. **Lớp Hạt Gió Bay Động (Wind Streamlines / Particles Layer)**:
     - Sử dụng HTML5 Canvas vẽ 150–200 hạt gió mảnh (Streamlines) chuyển động lướt trên bản đồ theo đúng góc hướng gió (Degree) và vận tốc gió (m/s).
     - Tạo hiệu ứng thị giác cực kỳ chuyên nghiệp và sống động (như các bản đồ khí tượng vệ tinh thế hệ mới).
  2. **Công cụ Chọn Tòa Nhà (Pick on Map Tool)**:
     - Bấm nút `[📍 Đo tại vị trí của tôi]` trên bản đồ: Cho phép di chuột bấm vào tòa nhà mong muốn (như S2.08, Ruby 1, Hải Âu 2).
     - Hiển thị Card nổi: *"Không khí tại Tòa S2.08: AQI 42 (Tốt), Nhiệt độ 28.5°C, Hướng gió Đông Nam 3.2 m/s"*.
  3. **Cắt Viền Đa Giác & Masking Bóng Đổ (Polygon Clamping)**:
     - Áp dụng thuật toán Ray-Casting 10 đỉnh cắt gọn mép heatmap, làm mờ vùng bên ngoài ranh giới dự án.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_spatial_dispersion.py -v
```

### 2.2. Test tương tác trực quan (Visual & Performance Test)
- [ ] Bật lớp Heatmap và lớp Hạt Gió:
  - Các vệt hạt gió chuyển động nhịp nhàng theo hướng gió hiện tại.
  - Tốc độ render duy trì mượt mà $\ge 50\text{ FPS}$ trên trình duyệt.
- [ ] Đổi hướng gió trong simulator từ $90^\circ$ (Đông) sang $270^\circ$ (Tây):
  - Hạt gió đổi chiều bay ngay lập tức và bản đồ nhiệt chuyển hướng lan tỏa tương ứng.
- [ ] Dùng công cụ Pick on Map nhấp vào giữa Hồ Ngọc Trai:
  - Thẻ kết quả hiển thị chỉ số AQI thấp hơn và nhiệt độ mát hơn các trạm ven đường.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ Hiệu ứng hạt gió hoạt động mượt mà, không gây rò rỉ bộ nhớ (Canvas cleanup on unmount).
2. ✅ Thuật toán IDW phản ánh chính xác tác động của vector gió và vùng mặt nước hồ điều hòa.
3. ✅ Thời gian tính toán nội suy điểm tùy chọn $< 50\text{ms}$.
