# Task B7-03: Bản Đồ Nhiệt Lan Truyền (IDW + Gió & Polygon Ocean Park 1)

> **Người phụ trách:** Backend Engineer & Frontend Map Specialist  
> **Thời hạn dự kiến:** Ngày 1 - Ngày 2  
> **Mục tiêu:** Hoàn thiện thuật toán nội suy không gian Inverse Distance Weighting có tính đến Vector Hướng & Vận tốc Gió (Wind-adjusted IDW), cắt gọt viền chính xác theo Polygon 10 đỉnh của Vinhomes Ocean Park 1, và bổ sung hoạt ảnh hạt gió sống động trên Canvas.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Spatial Engine
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/spatial_dispersion_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/spatial_dispersion_service.py)
  - [`backend/app/services/weather_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/weather_service.py)
  - [`backend/app/main.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/main.py) (Endpoint `/api/v1/spatial/dispersion`)
- **Nhiệm vụ cụ thể**:
  1. **Lưới không gian 30x30**: Chia khu vực tọa độ $[20.9840, 21.0050]$ vĩ độ và $[105.9330, 105.9630]$ kinh độ thành 900 điểm lưới.
  2. **Thuật toán Ray-Casting**: Kiểm tra từng điểm lưới xem có nằm trong đa giác 10 đỉnh của Vinhomes Ocean Park 1 hay không; loại bỏ các điểm ngoài ranh giới để giảm tải truyền tải và render.
  3. **Hiệu chỉnh Vector Gió**: Tính góc $\theta$ giữa hướng gió thực tế (từ OpenWeather API hoặc simulator) và vector trạm đo $\rightarrow$ điểm lưới:
     $$d_{\text{effective}} = \frac{d_{\text{Euclid}}}{1.0 + 0.15 \cdot \text{wind\_speed} \cdot \cos(\theta)}$$
     $$\text{Trọng số } w_i = \frac{1}{(d_{\text{effective}} + 0.0001)^2}$$
  4. **Quality Gate**: Nếu có ít hơn 3 trạm online/fresh $\rightarrow$ Trả về mã lỗi `insufficient_spatial_data` và không tính toán sai lệch.

### 1.2. Frontend Map Visualization
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/stations/HeatmapLayer.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/stations/HeatmapLayer.tsx)
  - [`frontend/src/features/map/OceanParkBoundary.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/OceanParkBoundary.tsx)
  - [`frontend/src/features/map/SuperMap.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/SuperMap.tsx)
- **Nhiệm vụ cụ thể**:
  1. **Tối ưu Canvas Rendering**: Sử dụng `leaflet.heat` hoặc Custom Canvas 2D để vẽ gradient màu mượt mà (Xanh ➔ Vàng ➔ Cam ➔ Đỏ ➔ Tím ➔ Nâu) theo bảng màu EPA AQI.
  2. **Lớp phủ Ranh giới (Polygon Mask)**: Phủ màu xám mờ ngoài ranh giới Ocean Park 1 để tôn vinh khu vực đô thị dự án.
  3. **Hiệu ứng Hạt Gió (Wind Particle Animation)**: Bổ sung lớp hạt chuyển động nhẹ nhàng theo hướng gió để bản đồ trở nên sinh động và tạo hiệu ứng WOW trước Ban Giám khảo.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_spatial_dispersion.py -v
```

### 2.2. Test thủ công trên Giao diện (Manual Checklist)
- [ ] Bật layer Heatmap trên bản đồ:
  - Bản đồ hiển thị dải màu mượt mà, bao trọn 5 trạm quan trắc.
  - Vùng xung quanh trạm có chỉ số cao (như S03) hiển thị màu đỏ/tím rõ rệt và bị dạt theo hướng gió.
- [ ] Thay đổi hướng gió từ Đông Nam ($135^\circ$) sang Tây Bắc ($315^\circ$) trong simulator:
  - Bản đồ nhiệt xoay hướng lan truyền ô nhiễm ngay trong chu kỳ làm mới tiếp theo.
- [ ] Tắt/Bật các layer phụ trợ (Sensor Markers, SubZone Labels): Không có xung đột visual.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ Endpoint `/api/v1/spatial/dispersion` phản hồi dưới $150\text{ms}$.
2. ✅ Tất cả 900 điểm lưới được lọc chính xác bằng thuật toán Ray-Casting 100% bên trong polygon.
3. ✅ Canvas Heatmap đạt tốc độ khung hình $60\text{ FPS}$ khi zoom/pan bản đồ.
