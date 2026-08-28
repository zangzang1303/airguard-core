# Task B7-01: Hoàn Thiện Dự Báo Ô Nhiễm 1–24h & Timeline Slider

> **Người phụ trách:** AI / ML Engineer & Frontend Lead  
> **Thời hạn dự kiến:** Ngày 1  
> **Mục tiêu:** Hoàn thiện và tinh chỉnh mô hình dự báo chuỗi thời gian 1–24h (Prophet Fourier) kết hợp Baseline 1–3h (Damped Linear Trend), đồng bộ mượt mà với thanh trượt Timeline Slider trên React Leaflet SuperMap.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend & ML Engine
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/prophet_forecast_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/prophet_forecast_service.py)
  - [`backend/app/services/forecast_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/forecast_service.py)
  - [`backend/app/main.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/main.py)
- **Nhiệm vụ cụ thể**:
  1. **Nâng cấp độ chính xác Fourier Seasonality**: Tinh chỉnh hệ số biến thiên giờ cao điểm giao thông (sáng 7–9h: $+8.5$ µg/m³, chiều 17–19h: $+11.0$ µg/m³) và ban đêm (22–05h: $+3.0$ µg/m³ do hiệu ứng nghịch nhiệt bề mặt).
  2. **Chuẩn hóa API Endpoint**: Đảm bảo endpoint `GET /api/v1/stations/{station_id}/forecast?hours=24&metric={metric}` trả về payload chuẩn có:
     - `predicted_value`, `lower_bound`, `upper_bound` (Khoảng tin cậy $1.645\sigma\sqrt{1+0.14h}$).
     - `hour_offset`, `timestamp` (ISO 8601 UTC+7).
     - `confidence_score` giảm dần theo chân trời dự báo ($0.92 - 0.012h$).
  3. **Cơ chế Fallback & Quality Gate**: Nếu trạm có ít hơn 3 điểm dữ liệu hợp lệ trong 72h ➔ Trả về mã lỗi có cấu trúc `insufficient_forecast_history` và fallback về giá trị đo gần nhất có ghi chú cảnh báo, không làm crash API.

### 1.2. Frontend UI / UX
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/stations/TimelineSlider.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/stations/TimelineSlider.tsx)
  - [`frontend/src/features/map/DraggableTimelineDock.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/DraggableTimelineDock.tsx)
  - [`frontend/src/features/map/SuperMap.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/SuperMap.tsx)
- **Nhiệm vụ cụ thể**:
  1. **Tương tác Kéo thả mượt mà (Draggable Dock)**: Cho phép người dùng kéo thả bảng điều khiển Timeline đến vị trí thuận tiện trên màn hình.
  2. **Đồng bộ thời gian thực với Heatmap**: Khi kéo slider sang mốc $+1\text{h}, +2\text{h}, +3\text{h}, \dots, +24\text{h}$, phát event `onForecastHourChange` để:
     - Lớp Heatmap (`HeatmapLayer.tsx`) tự động nạp lưới nội suy tương ứng giờ dự báo.
     - Các Marker trạm trên bản đồ cập nhật chỉ số AQI dự báo kèm nhãn `[Dự báo +Xh]`.
  3. **Biểu đồ Recharts mini trong Station Card**: Hiển thị đường xu hướng nét đứt (Dashed line) cho 24h tới kèm vùng mờ đại diện cho khoảng tin cậy (Confidence Interval).

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
Chạy lệnh kiểm thử benchmark và unit test:
```powershell
# 1. Chạy đánh giá MAE/RMSE mô hình Prophet so với Baseline
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\python" eval/run_prophet_benchmark.py

# 2. Chạy unit test API Forecast
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_agents/test_forecast.py tests/test_backend/test_forecast_api.py -v
```

### 2.2. Test thủ công trên Giao diện (Manual UI Checklist)
- [ ] Mở trình duyệt tại `http://localhost:5173`.
- [ ] Chọn tab bản đồ ➔ Bật chế độ xem **Heatmap** ➔ Bật thanh **Forecast Timeline**.
- [ ] Kéo slider từ `0h` lên `+1h`, `+2h`, `+3h`, `+6h`, `+12h`, `+24h`:
  - Bản đồ cập nhật màu sắc mượt mà không bị giật lag.
  - Nhãn giờ hiển thị chính xác theo giờ thực tế (VD: Hiện tại 21:00 ➔ +1h hiển thị 22:00, +2h hiển thị 23:00).
- [ ] Nhấp vào trạm **S03 (Hồ Ngọc Trai)**: Mở modal chi tiết trạm, kiểm tra tab "Dự báo 24h" có biểu đồ đường nét đứt rõ ràng.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ API phản hồi trong thời gian $< 250\text{ms}$ cho yêu cầu dự báo 24h của cả 5 trạm.
2. ✅ Sai số MAE của Prophet cải thiện $\ge 5\%$ so với Baseline trên tập test 72h.
3. ✅ Giao diện Timeline Slider không bị vỡ bố cục trên màn hình mobile và desktop.
4. ✅ Không có lỗi crash khi trạm bị mất tín hiệu (Offline/Stale).
