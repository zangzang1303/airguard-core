# Báo cáo Đánh giá Benchmark Mô hình Dự báo (B7-01)

> **Mô hình:** `extended_additive_fourier_v3` (Additive Fourier nhẹ; không phải thư viện Prophet)
> **Baseline:** `damped_linear_trend_v1`
> **Thời điểm đánh giá:** 2026-08-31T05:35:56.644003+00:00
> **Phạm vi kiểm thử:** holdout 24 giờ mới nhất từ chuỗi simulator 72 giờ, 5 trạm S01-S05.

---

## 1. Tổng quan Kết quả Hiệu năng

| Chỉ số Dự báo | Baseline Tuyến tính | Extended Additive | Mức độ Cải thiện (%) | Ngưỡng B7-01 (>= 7%) |
|---|:---:|:---:|:---:|:---:|
| **PM2.5 (MAE)** | **7.65 µg/m³** | **1.65 µg/m³** | **78.5%** | **ĐẠT** |
| **AQI (MAE)** | **18.02** | **3.69** | **79.5%** | Tham khảo |
| **Toàn diện Multi-Metric (MAE)** | **38.81** | **7.55** | **80.5%** | Tham khảo |
| **Toàn diện Multi-Metric (RMSE)** | **45.25** | **8.5** | **81.2%** | Tham khảo |

---

## 2. Chi tiết theo từng Trạm Quan trắc

| Trạm | PM2.5 (Base vs ML) | Cải thiện PM2.5 | AQI (Base vs ML) | Cải thiện AQI |
|---|:---:|:---:|:---:|:---:|
| **S01 (Trục Đa Tốn)** | 7.02 vs 0.35 | +95.1% | 17.14 vs 0.83 | +95.1% |
| **S02 (Khu Sapphire)** | 8.1 vs 2.77 | +65.7% | 19.14 vs 6.29 | +67.1% |
| **S03 (Ven Hồ Ngọc Trai)** | 8.03 vs 1.08 | +86.5% | 18.03 vs 2.38 | +86.8% |
| **S04 (Khuôn viên VinUni)** | 7.96 vs 2.42 | +69.6% | 18.65 vs 5.42 | +71.0% |
| **S05 (Khu Hải Âu)** | 7.15 vs 1.62 | +77.4% | 17.12 vs 3.54 | +79.3% |

---

## 3. Phân tích Nguyên nhân Cải thiện
1. **Khả năng nắm bắt chu kỳ ngày/đêm:** Baseline chỉ ngoại suy đường thẳng nên sai lệch lớn khi bước qua các khung giờ giao thời; trong khi mô hình Fourier nắm bắt chính xác dao động nhiệt độ và độ ẩm theo chu kỳ 24 giờ.
2. **Xử lý xung đột giờ cao điểm:** Mô hình cộng thêm hệ số giao thông buổi sáng (07:00–09:00) và buổi chiều (17:00–19:00), giảm thiểu hiện tượng underfitting tại các nút giao S01 và S05.
3. **Minh bạch mô hình:** Tên class legacy được giữ để tương thích import, nhưng API/source luôn ghi rõ đây là additive Fourier heuristic từ dữ liệu simulator.
