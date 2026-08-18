# Nâng cấp Dự báo Chuỗi thời gian (Prophet / Time-Series ML)

> **Người phụ trách:** Member 3 (AI Agent & ML Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 4  
> **Mục tiêu:** Xây dựng mô hình dự báo chuỗi thời gian ô nhiễm không khí nâng cao (Prophet / Lightweight ML) cho các khung giờ 6h, 12h, 24h tới, có đánh giá benchmark so sánh với baseline.

---

## 1. Kiến trúc Mô hình Dự báo

```text
Dữ liệu Lịch sử (24h - 7 ngày) + Yếu tố Thời tiết (Temp, Humidity, Wind)
                       │
                       ▼
             [Prophet / ML Engine]
   (Xử lý chu kỳ ngày/đêm + Hiệu ứng giờ cao điểm giao thông)
                       │
                       ▼
    Dự báo Điểm (Point Forecast) + Khoảng tin cậy (Lower/Upper Bound)
                       │
                       ▼
            API Endpoint & Agent Tool
```

---

## 2. Các bước triển khai

### Bước 1: Xây dựng Service Dự báo Prophet
* Tạo file: `backend/app/services/prophet_forecast_service.py` (hoặc lightweight statistical / time-series regression model).
* Đầu vào: Chuỗi dữ liệu đo của từng trạm (`measured_at`, `pm25`, `co2`, `temperature`, `humidity`).
* Đầu ra:
  ```json
  {
    "station_id": "S01",
    "metric": "pm25",
    "model": "prophet_time_series_v1",
    "horizons": [
      {"hours_ahead": 1, "timestamp": "2026-08-19T10:00:00Z", "predicted_value": 45.2, "lower_bound": 38.0, "upper_bound": 52.4},
      {"hours_ahead": 3, "timestamp": "2026-08-19T12:00:00Z", "predicted_value": 58.1, "lower_bound": 49.2, "upper_bound": 67.0},
      {"hours_ahead": 6, "timestamp": "2026-08-19T15:00:00Z", "predicted_value": 62.4, "lower_bound": 51.5, "upper_bound": 73.3},
      {"hours_ahead": 24, "timestamp": "2026-08-20T09:00:00Z", "predicted_value": 38.6, "lower_bound": 28.1, "upper_bound": 49.0}
    ],
    "trend_summary": "Dự kiến PM2.5 sẽ tăng mạnh vào giờ cao điểm trưa (11:00-13:00) và giảm dần vào chiều tối.",
    "confidence": "high"
  }
  ```

### Bước 2: Viết Script Đánh giá Model Benchmark (Evaluation Script)
* Tạo file: `eval/run_prophet_benchmark.py`.
* Chia dữ liệu thành tập Train (80%) và Test (20%).
* Tính toán các chỉ số:
  - **MAE (Mean Absolute Error)**: Sai số tuyệt đối trung bình.
  - **RMSE (Root Mean Squared Error)**: Căn bậc hai sai số bình phương trung bình.
  - So sánh trực tiếp giữa `damped_linear_trend_v1` và `prophet_time_series_v1`.
* Xuất báo cáo đánh giá vào file `docs/evidence/forecast-model-evaluation.md`.

### Bước 3: Cập nhật Tool cho AI Agent
* Bổ sung tool `get_extended_forecast` trong `src/agents/tools/`.
* Agent có thể trả lời các câu hỏi như:
  - *"Dự báo chất lượng không khí trong 24 giờ tới tại S01?"*
  - *"Chiều nay 17h tôi có thể chạy bộ quanh hồ được không?"*
  - *"Ngày mai thời điểm nào không khí trong lành nhất để mở cửa sổ thông thoáng nhà?"*

---

## 3. Tiêu chuẩn nghiệm thu

- [ ] Endpoint `GET /api/v1/stations/{id}/forecast?model=prophet&hours=24` trả về kết quả dự báo trong thời gian $< 500\text{ms}$.
- [ ] Chỉ số sai số MAE trên tập test tốt hơn baseline tuyến tính tối thiểu 15%.
- [ ] Agent diễn giải kết quả dự báo chính xác, có đầy đủ khoảng tin cậy và khuyến nghị cụ thể theo khung giờ.
