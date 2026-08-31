# Báo cáo Đánh giá Benchmark Mô hình Dự báo (B7-01)

> **Mô hình:** `extended_additive_fourier_v3` (Additive Fourier nhẹ; không phải thư viện Prophet)
> **Baseline:** `damped_linear_trend_v1`
> **Thời điểm đánh giá:** 2026-08-31T14:26:35.490527+00:00
> **Phạm vi kiểm thử:** holdout 24 giờ mới nhất từ chuỗi simulator 72 giờ, 5 trạm S01-S05.

---

## 1. Tổng quan Kết quả Hiệu năng

| Chỉ số Dự báo | Baseline Tuyến tính | Extended Additive | Mức độ Cải thiện (%) | Ngưỡng B7-01 (>= 7%) |
|---|:---:|:---:|:---:|:---:|
| **PM2.5 (MAE)** | **6.85 µg/m³** | **1.84 µg/m³** | **73.1%** | **ĐẠT** |
| **AQI (MAE)** | **15.84** | **4.15** | **73.8%** | Tham khảo |
| **Toàn diện Multi-Metric (MAE)** | **31.6** | **8.02** | **74.6%** | Tham khảo |
| **Toàn diện Multi-Metric (RMSE)** | **38.82** | **8.88** | **77.1%** | Tham khảo |

---

## 2. Chi tiết theo từng Trạm Quan trắc

| Trạm | PM2.5 (Base vs ML) | Cải thiện PM2.5 | AQI (Base vs ML) | Cải thiện AQI |
|---|:---:|:---:|:---:|:---:|
| **S01 (Trục Đa Tốn)** | 7.83 vs 2.04 | +73.9% | 19.29 vs 5.04 | +73.9% |
| **S02 (Khu Sapphire)** | 6.22 vs 2.11 | +66.0% | 15.22 vs 5.25 | +65.5% |
| **S03 (Ven Hồ Ngọc Trai)** | 6.26 vs 1.97 | +68.5% | 13.29 vs 4.33 | +67.4% |
| **S04 (Khuôn viên VinUni)** | 6.04 vs 2.5 | +58.6% | 12.73 vs 5.12 | +59.7% |
| **S05 (Khu Hải Âu)** | 7.92 vs 0.6 | +92.4% | 18.65 vs 1.0 | +94.6% |

---

## 3. Phân tích Nguyên nhân Cải thiện
1. **Khả năng nắm bắt chu kỳ ngày/đêm:** Baseline chỉ ngoại suy đường thẳng nên sai lệch lớn khi bước qua các khung giờ giao thời; trong khi mô hình Fourier nắm bắt chính xác dao động nhiệt độ và độ ẩm theo chu kỳ 24 giờ.
2. **Xử lý xung đột giờ cao điểm:** Mô hình cộng thêm hệ số giao thông buổi sáng (07:00–09:00) và buổi chiều (17:00–19:00), giảm thiểu hiện tượng underfitting tại các nút giao S01 và S05.
3. **Minh bạch mô hình:** Tên class legacy được giữ để tương thích import, nhưng API/source luôn ghi rõ đây là additive Fourier heuristic từ dữ liệu simulator.
