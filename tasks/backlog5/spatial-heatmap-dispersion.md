# Bản đồ nhiệt Lan truyền Ô nhiễm Không gian (Spatial IDW Heatmap)

> **Người phụ trách:** Member 2 (Backend) + Member 3 (AI Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 4  
> **Mục tiêu:** Xây dựng mô hình nội suy không gian (IDW) kết hợp hướng và vận tốc gió để tạo bản đồ nhiệt mô phỏng lan truyền ô nhiễm chân thực trong khu đô thị Vinhomes Ocean Park 1.

---

## 1. Phương pháp Thuật toán

### 1.1. Nội suy Trọng số Nghịch đảo Khoảng cách (IDW - Inverse Distance Weighting)
Với mỗi điểm lưới $(x, y)$ trong khu đô thị, nồng độ ước tính $C(x, y)$ từ $N=5$ trạm đo được tính theo công thức:
$$C(x, y) = \frac{\sum_{i=1}^{N} w_i C_i}{\sum_{i=1}^{N} w_i} \quad \text{với} \quad w_i = \frac{1}{(d_i + \epsilon)^p}$$
Trong đó:
- $C_i$: Nồng độ thực đo tại trạm $i$.
- $d_i$: Khoảng cách địa lý từ điểm $(x, y)$ đến trạm $i$.
- $p$: Hệ số suy giảm khoảng cách (mặc định $p=2.0$).
- $\epsilon$: Hằng số làm mịn tránh chia cho 0.

### 1.2. Hiệu chỉnh theo Hướng gió & Vận tốc gió (Wind Dispersion Vector)
Khoảng cách hiệu dụng $d_i^*$ được điều chỉnh dựa trên góc hợp giữa hướng từ trạm $i$ đến $(x, y)$ và hướng gió $\vec{V}_{wind}$:
- Nếu điểm nằm **xuôi chiều gió** từ nguồn ô nhiễm: Khoảng cách hiệu dụng $d_i^*$ giảm $\rightarrow$ Nồng độ lan xa hơn.
- Nếu điểm nằm **ngược chiều gió**: Khoảng cách hiệu dụng tăng $\rightarrow$ Nồng độ suy giảm nhanh hơn.

---

## 2. Các bước triển khai

### Bước 1: Xây dựng Backend Spatial Service
* Tạo file: `backend/app/services/spatial_dispersion_service.py`.
* Định nghĩa lưới điểm (Grid Matrix $30 \times 30$) bên trong ranh giới Polygon Ocean Park 1.
* Tạo API Endpoint:
  ```http
  GET /api/v1/spatial/heatmap?metric=aqi&forecast_hour=0
  ```
* Payload phản hồi:
  ```json
  {
    "metric": "aqi",
    "timestamp": "2026-08-19T09:00:00Z",
    "wind_speed_ms": 3.2,
    "wind_direction_deg": 135,
    "grid_points": [
      {"lat": 20.9912, "lon": 105.9521, "value": 72.4, "level": "moderate"},
      {"lat": 20.9915, "lon": 105.9525, "value": 115.8, "level": "unhealthy_sensitive"}
    ],
    "disclaimer": "Mô hình nội suy trực quan hóa IDW kết hợp vector khí tượng mô phỏng."
  }
  ```

### Bước 2: Tích hợp với Tool AI Agent
* Bổ sung tool `get_spatial_air_quality` giúp Agent có thể nhận biết và trả lời:
  - *"Khu vực quảng trường cá voi / hồ San Hô không khí thế nào so với khu biển nước mặn?"*
  - *"Gió hôm nay đang thổi ô nhiễm từ đường vành đai về khu căn hộ nào?"*

---

## 3. Tiêu chuẩn nghiệm thu

- [x] API trả về danh sách lưới điểm nội suy trong thời gian $< 200\text{ms}$.
- [x] Dữ liệu nội suy biến thiên mượt mà giữa các trạm, không bị răng cưa hay giá trị ngoại lai phi thực tế.
- [x] Khi tốc độ gió tăng, hình thái phân bố ô nhiễm dạt rõ rệt theo hướng xuôi gió.
- [x] Agent nhận diện câu hỏi so sánh POI/hướng gió, gọi `get_spatial_air_quality` và chỉ diễn giải grid cùng request.
- [x] Khi Spatial tool lỗi hoặc payload không qua data-quality gate, Agent trả insufficient-data và không dùng giá trị fixture.

## 4. Kết quả triển khai Người A — 21/08/2026

- Spatial model `idw-dispersion-v2.0` chỉ dùng tối thiểu ba trạm có tọa độ khác nhau, `online`, fresh, valid, có timestamp/source và metric nằm trong miền hợp lệ.
- Spatial service gọi `StationService` ở chế độ strict (`allow_fallback=False`), nên DB rỗng hoặc toàn bộ trạm stale/offline trả `insufficient_spatial_data` thay vì dùng simulator fallback; DB lỗi trả `spatial_station_data_unavailable` với HTTP 503.
- Mốc `forecast_hour=1..24` lấy giá trị từ forecast engine backend và loại station không đủ tối thiểu ba history point hợp lệ.
- Weather fallback được gắn `source`, `is_fallback`, `observed_at` và assumptions. Mốc tương lai ghi rõ giả định giữ nguyên vector gió hiện tại.
- Agent tool dùng input/output schema typed, kiểm tra metric, horizon, timestamp timezone-aware, data-quality và chặn NaN/Infinity.
- Agent router có intent `spatial`, catalog vị trí allow-list và composer deterministic. So sánh POI lấy điểm grid gần nhất; phân tích hướng gió được ghi rõ là suy luận hình học, không phải xác nhận nguồn phát thải.
- Typed Agent output giữ nguyên `model`, `extent` và `station_inputs`; adapter không còn loại bỏ các field provenance này sau validation.
- Frontend chỉ render grid do API trả về. Khi API lỗi hoặc thiếu dữ liệu, UI hiển thị error/retry và không tự sinh heatmap giả.

Kiểm chứng:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_backend\test_spatial_dispersion.py tests\test_backend\test_geospatial_agent.py tests\test_agents\test_tools.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_agents\test_grounding.py -k spatial -q
.\.venv\Scripts\ruff.exe check backend\app\services\station_service.py backend\app\services\spatial_dispersion_service.py src\agents\tools\contracts.py src\agents\tools\fake_adapter.py tests\test_backend\test_spatial_dispersion.py tests\test_agents\test_tools.py
Set-Location frontend
npm run build
```

Kết quả gần nhất: suite Spatial/backend/tool có `54 passed`; Agent Spatial routing/composer có `6 passed`; hai golden case Spatial đều pass; Ruff pass và frontend production build pass. Test contract xác minh `model`, `extent`, `station_inputs` được giữ sau validation và payload thiếu provenance bị trả `schema_drift`. Bốn test data source xác minh DB rỗng, DB lỗi, toàn bộ trạm stale/offline đều fail-closed và caller cũ vẫn giữ fallback mặc định để tương thích. Cảnh báo chunk frontend lớn hơn 500 kB là limitation hiệu năng bundle hiện hữu, không phải lỗi Spatial.

Smoke test hiệu năng với fixture simulator được truyền tường minh tạo 468 grid point từ đủ S01–S05 trong `5.69 ms` ở mốc hiện tại và `6.06 ms` ở forecast `+24h`; forecast source là `prophet_time_series_v1`. Luồng API thật không tự dùng fixture này.

Full regression tại cùng working tree: `232 passed`, không còn lỗi. Các lệch contract trước đó đã được sửa tại Agent fake adapter: history có station ID và thứ tự thời gian tăng dần; alert fixture giữ đúng rule-source/alert ID để grounding, evidence và proposal idempotency dùng cùng một provenance.

Giới hạn còn lại: đây là IDW trực quan có hiệu chỉnh gió; dữ liệu MVP có thể mang `source=simulator` sau khi được persist và qua quality gate, nhưng không phải mô hình lan truyền vật lý hay dữ liệu quan trắc được chứng nhận.

Integrator cần đồng bộ các field additive của Spatial response (`model`, `weather`, `data_quality`, `station_inputs`, `extent`) vào `specs/api-contracts.md` và frontend shared types khi tích hợp; Người A không sửa các file chung theo `parallel-work-coordination.md`.
