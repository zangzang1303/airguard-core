# Báo cáo Baseline Kiểm thử AI Agent (AirGuard AI)

> **Thời điểm lập:** 2026-08-23T22:11:00+07:00  
> **Phiên bản:** AirGuard AI Core v1.0.0  
> **Trạng thái hệ thống:** Đã kiểm thử 329 test cases (100% Passed)

---

## 1. Tổng quan Kiến trúc Pipeline AI Agent

Luồng xử lý yêu cầu người dùng trong AirGuard AI được thiết kế theo mô hình phân tầng chặt chẽ:

```text
User Query / Map Context / Selected Station
  │
  ▼
[1. Conversational Agent Gate] (`conversational_agent_service.py`)
  ├── Phân loại Intent: domain | greeting | social | clarification | out_of_scope
  └── Từ chối / phản hồi trực tiếp các câu chào hỏi, cảm ơn, hỏi ngoài phạm vi
  │
  ▼ (Nếu là domain query)
[2. Temporal Resolver] (`temporal_resolver.py`)
  ├── Giải mã thời gian: "hiện tại" (live) vs "tối nay", "chiều nay", "2h nữa" (forecast)
  └── Trích xuất giờ mục tiêu (forecast_hour, local_hour UTC+7)
  │
  ▼
[3. Multi-Source Telemetry Engine]
  ├── Live Telemetry (`live_telemetry_engine.py` / PostgreSQL repository)
  └── Prophet Time-Series ML Forecast (`prophet_forecast_service.py`)
  │
  ▼
[4. Geospatial Registry & Scoring Engine]
  ├── Registry POI & Tuyến đường (`spatial_registry.py`)
  ├── Chấm điểm phù hợp 5 trọng số (`environmental_scoring.py`):
  │   Score = 0.40*AQI + 0.25*PM2.5 + 0.15*Temp + 0.10*Noise + 0.10*Dist
  └── Cá nhân hóa theo nhóm sức khỏe (`HealthProfile`: normal vs sensitive vs sport)
  │
  ▼
[5. Intent Dispatcher & Response Synthesizer] (`geospatial_agent_service.py`)
  ├── Single Location / Parameter Focus (Nhiệt độ, Độ ồn, PM2.5, CO2)
  ├── Route Recommendation (Cung đường cố định hoặc tạo đường chạy tự động OSM)
  ├── Location Comparison (So sánh 2 khu vực, highlight cả 2 và fit bounds)
  ├── Worst / Best Location Identification (Tìm khu ô nhiễm nhất / sạch nhất)
  ├── Indoor Activity Pivot (Cảnh báo khi AQI > 150 -> Chuyển sang Bể bơi/Gym trong nhà)
  └── Weather / Precipitation Transparency (Giải thích giới hạn cảm biến đo mưa)
  │
  ▼
[6. Structured Map Action Controller & Frontend Rendering]
  ├── Declarative Map Actions (highlight_point, highlight_area, highlight_route, add_annotation, fly_to, fit_bounds)
  └── Frontend Leaflet AI Layer (`MapActionController.ts` & `SuperMap.tsx`)
```

---

## 2. Phân loại Dữ liệu trong Hệ thống

| Nhóm dữ liệu | Nguồn & Bản chất | Trạng thái | Đảm bảo Grounding |
|---|---|---|---|
| **Dữ liệu Cảm biến Hiện tại** | Telemetry từ 5 trạm quan trắc (S01–S05) qua MQTT / PostgreSQL | `source=simulator` | 100% Grounded, đọc từ `live_engine` / DB, không bịa đặt số |
| **Dữ liệu Dự báo 1h–24h** | Mô hình Prophet Time-Series ML (Fourier Decomposition + Giờ cao điểm) | `source=prophet_time_series_v1` | Có dải tin cậy $[Min, Max]$, đánh dấu rõ `FORECAST` |
| **Chỉ số AQI** | Tính toán theo quy chuẩn US EPA PM2.5 24h 2012 | `derived` | Tính toán bằng hàm toán học deterministic `pm25_aqi()` |
| **Bản đồ & Tọa độ POI** | Toạ độ thực tế khu đô thị Vinhomes Ocean Park 1 | `spatial_registry` | Dữ liệu hình học chuẩn OpenStreetMap, cấm tọa độ ảo |
| **Lộ trình Chạy bộ** | Đồ thị đường giao thông thực tế qua `RealRoadRoutingService` | `real_road_graph` | Đường chạy thật ven hồ/công viên, có cự ly km chính xác |
| **Cảnh báo & Đề xuất HITL** | Rule-based Alert Engine + Manager Approval workflow | `audit_logged` | Chỉ tạo proposal `pending`, cấm tự kích hoạt thiết bị |

---

## 3. Các Endpoint API Liên quan

1. **`POST /api/v1/agent/chat`**: Giao tiếp hội thoại và xử lý không gian với AI Agent (trả về Structured Answer + Declarative Map Actions).
2. **`GET /api/v1/stations` & `/api/v1/stations/{id}`**: Lấy danh sách và trạng thái cảm biến hiện tại.
3. **`GET /api/v1/stations/{id}/forecast` & `.../prophet`**: Lấy chuỗi dự báo môi trường 1h–24h.
4. **`GET /api/v1/alerts`**: Truy vấn danh sách cảnh báo môi trường chủ động.
5. **`GET /api/v1/proposals` & `POST /api/v1/proposals/{id}/approve`**: Hàng đợi phê duyệt HITL của Ban Quản lý.
6. **`GET /api/v1/spatial/dispersion`**: Bản đồ trường lan truyền ô nhiễm không gian Gaussian/IDW.

---

## 4. Kết quả Kiểm thử Baseline Hiện tại

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 329 items

tests/test_agents/ .................................................. [ 15%]
tests/test_api/ ..................................................... [ 38%]
tests/test_backend/ ................................................. [ 88%]
tests/test_iot/ ..................................................... [ 95%]
tests/test_scripts/ ................................................. [100%]

====================== 329 passed, 8 warnings in 11.53s =======================
```

---

## 5. Các Nguy cơ & Trọng tâm Cần Xử lý Tận gốc

1. **Nguy cơ Dynamic Data Inversion:** Khi telemetry cảm biến thay đổi đột ngột (ví dụ S01 từ 40 lên 190, S03 từ 165 xuống 45), Agent phải đảo ngược 100% kết quả xếp hạng và vùng highlight trên bản đồ, tuyệt đối không phụ thuộc cache cũ.
2. **Nguy cơ Nhầm lẫn Realtime vs Forecast:** Yêu cầu "hiện tại" bắt buộc đọc số đo mới nhất; yêu cầu "tối nay / 18:00" bắt buộc gọi mô hình dự báo và gán nhãn `FORECAST` rõ ràng.
3. **Nguy cơ Thiếu phân hóa theo Sức khỏe (Health Profile):** Cùng mức AQI 75, người bình thường có thể chạy bộ ngoài trời an toàn, nhưng người có bệnh lý hô hấp nhạy cảm phải nhận được điểm suitability thấp hơn và khuyến nghị phòng ngừa.
4. **Nguy cơ Bịa đặt Nguồn nguyên nhân (Causation Hallucination):** Agent không được tự ý khẳng định nguyên nhân ô nhiễm nếu trạm đo chưa có cảm biến chuyên dụng (phải nêu rõ dữ liệu tương quan vs suy đoán).
5. **Nguy cơ Bypass HITL:** Agent chỉ được sinh `WarningProposal` ở trạng thái `pending`, cấm xuất lệnh MQTT trực tiếp đến thiết bị ngoại vi.
