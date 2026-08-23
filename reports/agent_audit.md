# Báo cáo Audit & Sửa Tận Gốc AI Agent (AirGuard AI)

> **Thời điểm hoàn thành:** 2026-08-23T22:30:00+07:00  
> **Phiên bản:** AirGuard AI v1.0.0 Production Ready  
> **Trạng thái:** 344/344 Tests Passed (Tăng từ 329 ban đầu)

---

## 1. Kiến trúc Pipeline (Trước & Sau khi Audit)

### 🔴 Pipeline Ban đầu (Trước Audit)
```text
User Query ──> Simple Keyword Matching ──> Hardcoded Templates / Fallbacks
                   │
                   └──> Thiếu kiểm tra dải tin cậy
                   └──> Chưa tách bạch giữa thời gian hiện tại và dự báo
                   └──> Bị trôi bối cảnh bản đồ (stale context) khi hỏi tiếp
```

### 🟢 Pipeline Chuẩn hóa (Sau Audit Tận Gốc)
```text
User Query / Map Context / Selected Location
        │
        ▼
[1. Conversational Agent Gate] (`conversational_agent_service.py`)
  ├── Phân loại 5 Intent: domain | greeting | social | clarification | out_of_scope
  └── Từ chối & giải thích minh bạch khi hỏi ngoài phạm vi (Y tế, Mưa/Radar, Ẩm thực)
        │
        ▼ (Nếu là domain query)
[2. Temporal Resolver Engine] (`temporal_resolver.py`)
  ├── Nhận diện mốc thời gian: "hiện tại" (Live Mode) vs "tối nay / 18:00" (Forecast Mode)
  └── Đánh dấu rõ ràng cờ `is_forecast` và `data_mode`
        │
        ▼
[3. Multi-Source Grounded Telemetry]
  ├── Live Telemetry Store (`live_telemetry_engine.py`)
  └── Prophet Additive Fourier ML Forecast (`prophet_forecast_service.py`)
        │
        ▼
[4. Deterministic Scoring & Health Safety Evaluation] (`environmental_scoring.py`)
  ├── Công thức 5 trọng số: 0.40*AQI + 0.25*PM2.5 + 0.15*Temp + 0.10*Noise + 0.10*Dist
  ├── Cá nhân hóa sức khỏe: Phân biệt nhóm `normal` (người thường) vs `sensitive` (bệnh lý hô hấp)
  └── Indoor Activity Pivot: Khi AQI > 150 (hoặc > 100 với nhóm nhạy cảm) -> Tự động chuyển sang Bể bơi 4 mùa / VinUni Sports Complex
        │
        ▼
[5. Real Road Network Routing] (`real_road_routing_service.py`)
  └── Sinh tọa độ đường chạy thực tế theo đồ thị OpenStreetMap chuẩn theo km
        │
        ▼
[6. Structured Map Action Controller]
  └── Phát sinh Declarative Map Actions (Highlight Area, Annotation, Polyline Route, Fit Bounds)
```

---

## 2. Bảng Tổng hợp Lỗi, Nguyên nhân Gốc & Cách Khắc phục

| ID | Triệu chứng lỗi (Symptom) | Nguyên nhân gốc (Root Cause) | Giải pháp sửa tận gốc (Fix) |
|---|---|---|---|
| **BUG-01** | Hỏi *"Bây giờ ở San Hô có mưa không"* lại trả về template AQI/PM2.5. | `ConversationalAgentService` thiếu phân loại câu hỏi thời tiết/mưa ngoài phạm vi cảm biến. | Bổ sung `_handle_rain_or_precipitation_intent` giải thích rõ hệ thống chưa có radar đo mưa, đồng thời cung cấp vi khí hậu thực tế và hướng dẫn dùng app radar chuyên dụng. |
| **BUG-02** | Đảo ngược dữ liệu cảm biến (S01=190, S03=45), mô hình dự báo vẫn dùng giá trị cũ do bị pha loãng bởi lịch sử dài. | `prophet_service.forecast` tính `base_level` trên 12 điểm lịch sử, điểm override duy nhất bị pha loãng. | Cập nhật `LiveTelemetryEngine.update_station` đồng bộ 5 điểm gần nhất, đảm bảo mô hình dự báo tức thời nhận biết trạng thái ô nhiễm mới. |
| **BUG-03** | Hỏi *"PM2.5 ở S03 hiện tại là bao nhiêu?"* nhưng rơi vào recommendation chung thay vì trả về trạm S03. | `spatial_registry.find_poi_by_name` chỉ tìm theo tên POI mà chưa hỗ trợ regex mã trạm (`S01-S05`). | Bổ sung regex matching `\b(s0[1-5])\b` trong `find_poi_by_name`, tự động liên kết mã trạm với POI tương ứng. |
| **BUG-04** | Người dùng hỏi câu tiếp theo *"Còn chỗ này?"* khi đang click trạm S01 bị rơi vào gợi ý mặc định. | Thiếu các cụm từ ngữ cảnh tiếp diễn (*"chỗ này", "ở đây", "khu này"*) trong điều kiện kích hoạt Single Location Intent. | Mở rộng bộ phân loại ngữ cảnh tiếp nối trong `geospatial_agent_service.py` để ưu tiên `selected_location` và `selected_sensor`. |
| **BUG-05** | Nhóm người nhạy cảm (`sensitive`) tại mức AQI 115 không được phân biệt rõ với người bình thường. | `environmental_scoring.py` chỉ dùng 1 ngưỡng chung AQI 150 cho mọi đối tượng. | Bổ sung ngưỡng nghiêm ngặt cho nhóm nhạy cảm (AQI > 100, PM2.5 > 50) và trả về cảnh báo chuyên biệt cho đường thở. |

---

## 3. Bảng Đối chiếu Kiểm thử (Before vs After)

| Hạng mục kiểm thử | Trước Audit | Sau Audit Tận Gốc | Trạng thái |
|---|:---:|:---:|:---:|
| **Tổng số Unit / Integration Tests** | 329 Passed | **344 Passed** (+15 comprehensive tests) | ✅ **100% Passed** |
| **Dynamic Data Inversion (Đảo ngược dữ liệu)** | Chưa có test kiểm soát | Đã có test kiểm chứng tự động | ✅ **ĐẠT** |
| **Realtime vs Forecast Tagging** | Dễ nhầm lẫn | Tách bạch 100% qua `data_mode` | ✅ **ĐẠT** |
| **Map Actions Declarative Schema** | Cơ bản | Chuẩn hóa 6 action types + Validate Bounds | ✅ **ĐẠT** |
| **Prompt Injection Defense** | Chưa có kiểm tra | Dữ liệu Grounded thắng lệnh người dùng | ✅ **ĐẠT** |
| **Tập Eval Dataset Chuẩn hóa** | 5 live cases | **25 Test Cases đầy đủ các phân nhánh** | ✅ **ĐẠT** |

---

## 4. Danh sách Công cụ & Thuật toán Định lượng (Deterministic Tools)

1. **`EnvironmentalScoringEngine.score_candidate`**:
   $$\text{Score} = 0.40 \times S_{\text{AQI}} + 0.25 \times S_{\text{PM2.5}} + 0.15 \times S_{\text{Temp}} + 0.10 \times S_{\text{Noise}} + 0.10 \times S_{\text{Dist}}$$
2. **`EnvironmentalScoringEngine.check_outdoor_exercise_safety`**:
   - Nhóm thông thường: Cho phép tập ngoài trời khi $\text{AQI} \le 150$ và $\text{PM2.5} \le 75\ \mu\text{g/m}^3$.
   - Nhóm nhạy cảm hô hấp: Giới hạn nghiêm ngặt $\text{AQI} \le 100$ và $\text{PM2.5} \le 50\ \mu\text{g/m}^3$.
3. **`RealRoadRoutingService.generate_exact_running_route`**:
   - Sử dụng đồ thị giao thông thực tế OpenStreetMap tại Vinhomes Ocean Park 1, tính toán cự ly thực tế theo km.
4. **`ProphetForecastService.forecast`**:
   - Phân rã chuỗi thời gian Fourier Additive + Hệ số giờ cao điểm giao thông buổi sáng (07:00–09:00) và buổi chiều (17:00–19:00).

---

## 5. Giới hạn Đã biết (Known Limitations)

- **Cảm biến lượng mưa:** AirGuard AI hiện tại là hệ thống quan trắc chất lượng không khí và vi khí hậu vi mô; hệ thống chưa có cảm biến đo lượng mưa chuyên dụng hay radar mây vệ tinh thời gian thực (được thông báo rõ cho người dùng khi hỏi về thời tiết mưa).
- **Phạm vi địa lý:** Hệ thống được thiết kế tối ưu cho khu vực đô thị Vinhomes Ocean Park 1 với 5 trạm quan trắc S01–S05.
