# Báo cáo Đánh giá Benchmark Mô hình Dự báo (B7-01)

> **Mô hình:** `extended_additive_fourier_v3` (Additive Fourier nhẹ; không phải thư viện Prophet)
> **Baseline:** `damped_linear_trend_v1`
> **Thời điểm đánh giá:** 2026-08-30T08:29:26.342952+00:00
> **Phạm vi kiểm thử:** holdout 24 giờ mới nhất từ chuỗi simulator 72 giờ, 5 trạm S01-S05.

---

## 1. Tổng quan Kết quả Hiệu năng

| Chỉ số Dự báo | Baseline Tuyến tính | Extended Additive | Mức độ Cải thiện (%) | Ngưỡng B7-01 (>= 7%) |
|---|:---:|:---:|:---:|:---:|
| **PM2.5 (MAE)** | **5.65 µg/m³** | **1.84 µg/m³** | **67.5%** | **ĐẠT** |
| **AQI (MAE)** | **12.84** | **4.17** | **67.5%** | Tham khảo |
| **Toàn diện Multi-Metric (MAE)** | **27.44** | **7.97** | **71.0%** | Tham khảo |
| **Toàn diện Multi-Metric (RMSE)** | **34.88** | **8.81** | **74.7%** | Tham khảo |

---

## 2. Chi tiết theo từng Trạm Quan trắc

| Trạm | PM2.5 (Base vs ML) | Cải thiện PM2.5 | AQI (Base vs ML) | Cải thiện AQI |
|---|:---:|:---:|:---:|:---:|
| **S01 (Trục Đa Tốn)** | 5.6 vs 2.9 | +48.1% | 13.32 vs 6.75 | +49.3% |
| **S02 (Khu Sapphire)** | 5.87 vs 0.21 | +96.4% | 14.28 vs 0.54 | +96.2% |
| **S03 (Ven Hồ Ngọc Trai)** | 5.72 vs 2.66 | +53.5% | 12.25 vs 6.12 | +50.0% |
| **S04 (Khuôn viên VinUni)** | 5.43 vs 0.84 | +84.6% | 11.66 vs 1.83 | +84.3% |
| **S05 (Khu Hải Âu)** | 5.62 vs 2.58 | +54.0% | 12.69 vs 5.62 | +55.7% |

---

## 3. Phân tích Nguyên nhân Cải thiện
1. **Khả năng nắm bắt chu kỳ ngày/đêm:** Baseline chỉ ngoại suy đường thẳng nên sai lệch lớn khi bước qua các khung giờ giao thời; trong khi mô hình Fourier nắm bắt chính xác dao động nhiệt độ và độ ẩm theo chu kỳ 24 giờ.
2. **Xử lý xung đột giờ cao điểm:** Mô hình cộng thêm hệ số giao thông buổi sáng (07:00–09:00) và buổi chiều (17:00–19:00), giảm thiểu hiện tượng underfitting tại các nút giao S01 và S05.
3. **Minh bạch mô hình:** Tên class legacy được giữ để tương thích import, nhưng API/source luôn ghi rõ đây là additive Fourier heuristic từ dữ liệu simulator.
