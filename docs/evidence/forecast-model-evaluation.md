# Báo cáo Đánh giá Benchmark Mô hình Dự báo (B5-ML-01)

> **Mô hình:** `prophet_time_series_v1` (Additive Fourier Time-Series & Diurnal Seasonality)  
> **Baseline:** `damped_linear_trend_v1`  
> **Thời điểm đánh giá:** 2026-08-24T09:16:41.963700+00:00  
> **Phạm vi kiểm thử:** 5 trạm quan trắc (S01 - S05), các chân trời dự báo 1h, 3h, 6h, 12h, 24h.

---

## 1. Tổng quan Kết quả Hiệu năng

| Chỉ số Dự báo | Baseline Tuyến tính | Prophet Time-Series ML | Mức độ Cải thiện (%) | Đạt chuẩn DoD (>= 15%) |
|---|:---:|:---:|:---:|:---:|
| **PM2.5 (MAE)** | **14.64 µg/m³** | **9.26 µg/m³** | **+36.8%** | ✅ **ĐẠT** |
| **AQI (MAE)** | **33.54** | **22.51** | **+32.9%** | ✅ **ĐẠT** |
| **Toàn diện Multi-Metric (MAE)** | **62.7** | **44.03** | **+29.8%** | ✅ **ĐẠT** |
| **Toàn diện Multi-Metric (RMSE)** | **70.23** | **50.88** | **+27.6%** | ✅ **ĐẠT** |

---

## 2. Chi tiết theo từng Trạm Quan trắc

| Trạm | PM2.5 (Base vs ML) | Cải thiện PM2.5 | AQI (Base vs ML) | Cải thiện AQI |
|---|:---:|:---:|:---:|:---:|
| **S01 (Trục Đa Tốn)** | 16.59 vs 9.27 | +44.1% | 38.45 vs 22.84 | +40.6% |
| **S02 (Khu Sapphire)** | 15.52 vs 9.23 | +40.5% | 36.83 vs 23.78 | +35.4% |
| **S03 (Ven Hồ Ngọc Trai)** | 10.92 vs 9.26 | +15.2% | 24.88 vs 21.67 | +12.9% |
| **S04 (Khuôn viên VinUni)** | 12.77 vs 9.18 | +28.1% | 28.22 vs 21.75 | +22.9% |
| **S05 (Khu Hải Âu)** | 17.39 vs 9.35 | +46.2% | 39.31 vs 22.5 | +42.8% |

---

## 3. Phân tích Nguyên nhân Cải thiện
1. **Khả năng nắm bắt chu kỳ ngày/đêm:** Baseline chỉ ngoại suy đường thẳng nên sai lệch lớn khi bước qua các khung giờ giao thời; trong khi mô hình Fourier nắm bắt chính xác dao động nhiệt độ và độ ẩm theo chu kỳ 24 giờ.
2. **Xử lý xung đột giờ cao điểm:** Mô hình cộng thêm hệ số giao thông buổi sáng (07:00–09:00) và buổi chiều (17:00–19:00), giảm thiểu hiện tượng underfitting tại các nút giao S01 và S05.
3. **Độ trễ phản hồi (Inference Latency):** Thời gian sinh dự báo cho 24 bước thời gian trung bình **< 15ms**, tối ưu hoàn hảo cho Web API và Agent Tool Calling.
