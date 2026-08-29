# Task B7-01: Dự Báo Ô Nhiễm 1–24h Đa Biến, Khung Giờ Vàng & Animation Tua Nhanh

> **Trạng thái triển khai (29/08/2026): Hoàn thành code và automated verification bằng lightweight additive Fourier.** Tên
> class `ProphetForecastService` được giữ tương thích import, nhưng model/source/API ghi rõ đây
> không phải thư viện Prophet. Benchmark time-aligned đạt PM2.5 MAE cải thiện 75,6% trên holdout
> 24h từ chuỗi simulator 72h. API, Agent 1–24h, golden windows, Play/Pause 800ms, confidence chart
> và frontend production build đã được kiểm thử tự động; checklist thao tác trình duyệt vẫn cần
> chạy trong buổi nghiệm thu live.

> **Người phụ trách:** AI / ML Engineer & Frontend Lead  
> **Thời hạn dự kiến:** Ngày 1  
> **Mục tiêu:** 
> 1. Xây dựng mô hình dự báo chuỗi thời gian 1–24h kết hợp đa biến khí tượng (Độ ẩm, Nhiệt độ, Nghịch nhiệt ban đêm, Giờ cao điểm giao thông) với khoảng tin cậy mở rộng theo thời gian.
> 2. Tính năng **"Khung Giờ Vàng" (Golden Air Windows)**: Tự động phát hiện và gợi ý thời điểm không khí trong lành nhất để mở cửa thông thoáng nhà hoặc chạy bộ.
> 3. Giao diện **"Play / Pause 24h Simulation"**: Nút bấm tự động chạy animation diễn biến ô nhiễm 24h tới trên bản đồ nhiệt tương tự các đài khí tượng quốc tế.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend & ML Engine
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/prophet_forecast_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/prophet_forecast_service.py)
  - [`backend/app/services/forecast_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/forecast_service.py)
  - [`backend/app/main.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/main.py) (Endpoint `/api/v1/stations/{id}/forecast`, `/api/v1/forecast/golden-windows`)
- **Nhiệm vụ cụ thể**:
  1. **Dự báo Đa biến Khí tượng Thực tế (Multi-variate Weather Interaction)**:
     - **Hiệu ứng Nghịch nhiệt Bề mặt (Nocturnal Thermal Inversion)**: Vào ban đêm (22:00 - 05:00), khi nhiệt độ bề mặt đất giảm nhanh và độ ẩm $> 80\%$, lớp khí lạnh bị giữ sát mặt đất khiến bụi mịn PM2.5 khó khuếch tán $\rightarrow$ Áp dụng hệ số cộng dồn $+3.5\text{ µg/m³}$.
     - **Đỉnh Cao Điểm Giao Thông (Traffic Rush Peaks)**: Tác động vào trục Đa Tốn (S01) và Hải Âu (S05) vào 07:00–09:00 ($+8.5\text{ µg/m³}$) và 17:00–19:00 ($+11.0\text{ µg/m³}$).
  2. **Thuật toán Khai phá Khung Giờ Vàng (Golden Windows Algorithm)**:
     - Quét chuỗi 24 điểm dự báo để trích xuất:
       * **Best Window (Mở cửa/Tập thể dục)**: Khoảng thời gian liên tục $\ge 2\text{ giờ}$ có $\text{AQI} \le 50$ và vận tốc gió tốt.
       * **Worst Window (Đóng cửa/Tránh ra ngoài)**: Khung giờ có AQI đạt đỉnh cao nhất trong 24h tới.
  3. **Khoảng Tin Cậy Xác Suất Chuẩn (Calibrated Uncertainty Bounds)**:
     $$\text{Predicted}(t) = \text{BaseLevel} + g(t) + s_1(t) + s_2(t) + r(t) + m(t)$$
     $$\text{Lower} / \text{Upper} = \text{Predicted}(t) \pm 1.645 \cdot \sigma_{\text{residual}} \sqrt{1 + 0.14 \cdot h}$$

---

### 1.2. Frontend UI / UX & Animation Tua Nhanh 24h
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/stations/TimelineSlider.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/stations/TimelineSlider.tsx)
  - [`frontend/src/features/map/DraggableTimelineDock.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/DraggableTimelineDock.tsx)
  - [`frontend/src/features/map/SuperMap.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/SuperMap.tsx)
- **Nhiệm vụ cụ thể**:
  1. **Nút Play / Pause Tự Động Tua 24h**:
     - Nút `[▶ Play Simulation]` trên Timeline Dock: Tự động tăng từng giờ ($+0\text{h} \rightarrow +1\text{h} \rightarrow +2\text{h} \dots \rightarrow +24\text{h}$) mỗi $800\text{ms}$.
     - Lớp Heatmap và nhãn trạm biến đổi màu sắc liên tục theo dòng thời gian, giúp người xem nhìn thấy rõ "đợt sóng ô nhiễm" di chuyển qua khu đô thị.
  2. **Thẻ Badge "Khung Giờ Vàng" Thông Minh**:
     - Hiển thị widget mini trên góc bản đồ: *"🌿 Khung giờ vàng mở cửa nhà: 05:30 - 08:00 sáng mai (AQI 28)"* và *"⚠️ Đỉnh ô nhiễm cần tránh: 18:00 chiều nay (AQI 142)"*.
  3. **Biểu đồ Recharts 24h Đa tầng**:
     - Hiển thị đường nét liền cho giá trị hiện tại, nét đứt cho 24h dự báo, kèm dải màu nền mờ thể hiện khoảng tin cậy.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\python" eval/run_prophet_benchmark.py
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_forecast_api.py tests/test_agents/test_forecast.py -v
```

### 2.2. Test thủ công trên Giao diện (Manual UI Checklist)
- [ ] Bật Heatmap ➔ Bấm nút **[Play Simulation]**:
  - Thanh slider tự động chạy từ $+0\text{h}$ đến $+24\text{h}$.
  - Bản đồ chuyển đổi mượt mà giữa các giờ.
  - Bấm `[Pause]` để dừng ở một mốc giờ cụ thể.
- [ ] Kiểm tra widget Khung Giờ Vàng: Gợi ý đúng khung giờ có AQI thấp nhất trong 24h tới.
- [ ] Mở Chat AI hỏi: *"Sáng mai mấy giờ mở cửa sổ tốt nhất?"* $\rightarrow$ AI trả lời chính xác dựa trên Khung Giờ Vàng của mô hình dự báo.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ Sai số MAE của Prophet cải thiện $\ge 7\%$ so với baseline trên tập test 72h.
2. 🟡 Animation Play 24h đã pass contract test và production build; độ mượt/memory leak cần xác nhận bằng checklist trình duyệt live khi Docker daemon hoạt động.
3. ✅ Khung Giờ Vàng được tính toán tự động và có căn cứ khoa học rõ ràng.
