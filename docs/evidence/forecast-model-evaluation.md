# Báo cáo Đánh giá Benchmark Mô hình Dự báo (B7-01)

> **Mô hình:** `extended_additive_fourier_v3` (Additive Fourier nhẹ; không phải thư viện Prophet)
> **Baseline:** `damped_linear_trend_v1`
> **Thời điểm đánh giá:** 2026-08-29T05:58:15.030529+00:00
> **Phạm vi kiểm thử:** holdout 24 giờ mới nhất từ chuỗi simulator 72 giờ, 5 trạm S01-S05.

---

## 1. Tổng quan Kết quả Hiệu năng

| Chỉ số Dự báo | Baseline Tuyến tính | Extended Additive | Mức độ Cải thiện (%) | Ngưỡng B7-01 (>= 7%) |
|---|:---:|:---:|:---:|:---:|
| **PM2.5 (MAE)** | **7.67 µg/m³** | **1.87 µg/m³** | **75.6%** | **ĐẠT** |
| **AQI (MAE)** | **17.54** | **4.13** | **76.4%** | Tham khảo |
| **Toàn diện Multi-Metric (MAE)** | **38.82** | **7.39** | **81.0%** | Tham khảo |
| **Toàn diện Multi-Metric (RMSE)** | **45.3** | **8.51** | **81.2%** | Tham khảo |

---

## 2. Chi tiết theo từng Trạm Quan trắc

| Trạm | PM2.5 (Base vs ML) | Cải thiện PM2.5 | AQI (Base vs ML) | Cải thiện AQI |
|---|:---:|:---:|:---:|:---:|
| **S01 (Trục Đa Tốn)** | 7.1 vs 2.5 | +64.9% | 17.35 vs 6.21 | +64.2% |
| **S02 (Khu Sapphire)** | 7.85 vs 0.92 | +88.3% | 19.23 vs 2.25 | +88.3% |
| **S03 (Ven Hồ Ngọc Trai)** | 8.08 vs 2.82 | +65.0% | 17.04 vs 6.0 | +64.8% |
| **S04 (Khuôn viên VinUni)** | 8.22 vs 0.38 | +95.4% | 17.71 vs 0.67 | +96.2% |
| **S05 (Khu Hải Âu)** | 7.11 vs 2.73 | +61.6% | 16.36 vs 5.54 | +66.1% |

---

## 3. Phân tích Nguyên nhân Cải thiện
1. **Khả năng nắm bắt chu kỳ ngày/đêm:** Baseline chỉ ngoại suy đường thẳng nên sai lệch lớn khi bước qua các khung giờ giao thời; trong khi mô hình Fourier nắm bắt chính xác dao động nhiệt độ và độ ẩm theo chu kỳ 24 giờ.
2. **Xử lý xung đột giờ cao điểm:** Mô hình cộng thêm hệ số giao thông buổi sáng (07:00–09:00) và buổi chiều (17:00–19:00), giảm thiểu hiện tượng underfitting tại các nút giao S01 và S05.
3. **Minh bạch mô hình:** Tên class legacy được giữ để tương thích import, nhưng API/source luôn ghi rõ đây là additive Fourier heuristic từ dữ liệu simulator.
