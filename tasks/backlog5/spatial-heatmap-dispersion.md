# Bản đồ nhiệt Lan truyền Ô nhiễm Không gian (Spatial IDW Heatmap)

> **Người phụ trách:** Member 2 (Backend) + Member 3 (AI Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 4  
> **Mục tiêu:** Xây dựng mô hình nội suy không gian (IDW) kết hợp hướng và vận tốc gió để tạo bản đồ nhiệt mô phỏng lan truyền ô nhiễm chân thực trong khu đô thị Vinhomes Ocean Park 1.

---

## 1. Phương pháp Thuật toán

### 1.1. Nội suy Trọng số Nghịch đảo Khoảng cách (IDW - Inverse Distance Weighting)
Với mỗi điểm lưới $(x, y)$ trong khu đô thị, nồng độ ước tính $C(x, y)$ từ $N=5$ trạm đo được tính theo công thức:
$$C(x, y) = \frac{\sum_{i=1}^{N} w_i C_i}{\sum_{i=1}^{N} w_i} \quad \text{với} \quad w_i = \frac{1}{(d_i + \epsilon)^p}$$
Trong đó:
- $C_i$: Nồng độ thực đo tại trạm $i$.
- $d_i$: Khoảng cách địa lý từ điểm $(x, y)$ đến trạm $i$.
- $p$: Hệ số suy giảm khoảng cách (mặc định $p=2.0$).
- $\epsilon$: Hằng số làm mịn tránh chia cho 0.

### 1.2. Hiệu chỉnh theo Hướng gió & Vận tốc gió (Wind Dispersion Vector)
Khoảng cách hiệu dụng $d_i^*$ được điều chỉnh dựa trên góc hợp giữa hướng từ trạm $i$ đến $(x, y)$ và hướng gió $\vec{V}_{wind}$:
- Nếu điểm nằm **xuôi chiều gió** từ nguồn ô nhiễm: Khoảng cách hiệu dụng $d_i^*$ giảm $\rightarrow$ Nồng độ lan xa hơn.
- Nếu điểm nằm **ngược chiều gió**: Khoảng cách hiệu dụng tăng $\rightarrow$ Nồng độ suy giảm nhanh hơn.

---

## 2. Các bước triển khai

### Bước 1: Xây dựng Backend Spatial Service
* Tạo file: `backend/app/services/spatial_dispersion_service.py`.
* Định nghĩa lưới điểm (Grid Matrix $30 \times 30$) bên trong ranh giới Polygon Ocean Park 1.
* Tạo API Endpoint:
  ```http
  GET /api/v1/spatial/heatmap?metric=aqi&forecast_hour=0
  ```
* Payload phản hồi:
  ```json
  {
    "metric": "aqi",
    "timestamp": "2026-08-19T09:00:00Z",
    "wind_speed_ms": 3.2,
    "wind_direction_deg": 135,
    "grid_points": [
      {"lat": 20.9912, "lon": 105.9521, "value": 72.4, "level": "moderate"},
      {"lat": 20.9915, "lon": 105.9525, "value": 115.8, "level": "unhealthy_sensitive"}
    ],
    "disclaimer": "Mô hình nội suy trực quan hóa IDW kết hợp vector khí tượng mô phỏng."
  }
  ```

### Bước 2: Tích hợp với Tool AI Agent
* Bổ sung tool `get_spatial_air_quality` giúp Agent có thể nhận biết và trả lời:
  - *"Khu vực quảng trường cá voi / hồ San Hô không khí thế nào so với khu biển nước mặn?"*
  - *"Gió hôm nay đang thổi ô nhiễm từ đường vành đai về khu căn hộ nào?"*

---

## 3. Tiêu chuẩn nghiệm thu

- [ ] API trả về danh sách lưới điểm nội suy trong thời gian $< 200\text{ms}$.
- [ ] Dữ liệu nội suy biến thiên mượt mà giữa các trạm, không bị răng cưa hay giá trị ngoại lai phi thực tế.
- [ ] Khi tốc độ gió tăng, hình thái phân bố ô nhiễm dạt rõ rệt theo hướng xuôi gió.
