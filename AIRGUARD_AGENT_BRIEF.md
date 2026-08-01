# AIRGUARD AI — Agent Implementation Brief

Tài liệu này dùng để đưa cho coding agent trong VS Code. Mục tiêu là tạo một repository đủ rõ ràng, có cấu trúc, có tài liệu, có prototype tối thiểu và có thể push lên GitHub trước buổi coaching.

---

## 0. Mục tiêu cần đạt ngay

Cần hoàn thành một bản repository ban đầu cho dự án **AirGuard AI** với các phần sau:

1. Tài liệu hóa đầy đủ:
   - Vấn đề đang gặp.
   - Giải pháp đề xuất.
   - Mục tiêu SMART 6 tuần.
   - In-scope / Out-of-scope.
   - Kiến trúc hệ thống.
   - Mô hình dữ liệu.
   - User stories.
   - Backlog.
   - Phân công nhóm 4 người.

2. Có prototype kỹ thuật tối thiểu:
   - Sensor Simulator sinh dữ liệu PM2.5 giả lập.
   - MQTT topic design.
   - FastAPI backend skeleton.
   - PostgreSQL schema ban đầu.
   - React Leaflet map skeleton hoặc hướng dẫn chạy.
   - 5 điểm cảm biến PM2.5 trên bản đồ thật.

3. Có thể push lên GitHub với cấu trúc repo rõ ràng.

Không cần hoàn thành toàn bộ sản phẩm. Chỉ cần đủ để chứng minh nhóm đã chuyển từ ý tưởng sang thiết kế và prototype ban đầu.

---

## 1. Tóm tắt project

**Tên dự án:** AirGuard AI  
**Mục tiêu:** Xây dựng AI Agent giám sát chất lượng không khí ngoài trời trong khu đô thị/campus, tập trung vào chỉ số bụi mịn PM2.5.

Hệ thống sử dụng:

- Bản đồ thật.
- 5 điểm cảm biến PM2.5 giả lập.
- MQTT để truyền dữ liệu cảm biến.
- API thời tiết thực tế để lấy nhiệt độ, độ ẩm, gió và mưa.
- FastAPI backend.
- PostgreSQL database.
- Forecast Service dự báo PM2.5 trong 1–3 giờ.
- AI Agent để giải thích, cảnh báo và khuyến nghị.
- React Leaflet Dashboard.
- HITL để ban quản lý phê duyệt cảnh báo diện rộng hoặc lệnh thiết bị giả lập.

Câu mô tả ngắn:

> AirGuard AI là hệ thống AI Agent giám sát PM2.5 ngoài trời trong một khu đô thị/campus giới hạn, sử dụng bản đồ thật, cảm biến giả lập qua MQTT và dữ liệu thời tiết thực tế để theo dõi, dự báo, cảnh báo và đưa ra khuyến nghị cho người dùng. Các cảnh báo diện rộng hoặc lệnh liên động thiết bị phải được quản lý phê duyệt qua HITL.

---

## 2. Phạm vi MVP

### 2.1. In-scope

- Giám sát PM2.5 ngoài trời tại tối thiểu 5 điểm trong một khu đô thị/campus.
- Dùng bản đồ thật để hiển thị vị trí cảm biến.
- Cảm biến PM2.5 giả lập gửi dữ liệu qua MQTT.
- Kết hợp API thời tiết thực tế.
- Backend nhận, kiểm tra và lưu dữ liệu.
- Dashboard hiển thị marker cảm biến, PM2.5 hiện tại và trạng thái.
- Dự báo PM2.5 trong 1–3 giờ.
- AI Agent giải thích tình trạng môi trường và đưa khuyến nghị.
- Có ít nhất 3 nhóm người dùng:
  - Người dùng thông thường.
  - Người nhạy cảm với ô nhiễm.
  - Người hoạt động thể thao ngoài trời.
- HITL cho cảnh báo diện rộng và lệnh thiết bị giả lập.
- Một thiết bị thông gió/lọc khí giả lập qua MQTT.
- Docker Compose cho các service chính.

### 2.2. Out-of-scope

- Không triển khai trên toàn thành phố.
- Không lắp cảm biến vật lý thật.
- Không điều khiển thiết bị HVAC/BMS thật.
- Không tập trung vào PM10, CO2, NO2, SO2, O3, tiếng ồn trong MVP.
- Không chẩn đoán hoặc tư vấn y tế.
- Không tích hợp bệnh án thật.
- Không cần app mobile riêng.
- Không cần mô hình deep learning phức tạp.
- Không cần route optimization/tuyến đường ít ô nhiễm ở giai đoạn đầu.

---

## 3. Khu vực bản đồ thật và 5 điểm cảm biến

Nếu chưa chốt tọa độ thật, dùng tạm khu vực **VinUniversity / Vinhomes Ocean Park** làm khu vực demo. Sau đó team có thể sửa lại tọa độ.

> Lưu ý: các tọa độ dưới đây chỉ là mẫu gần đúng để prototype chạy được. Trước khi demo, cần mở OpenStreetMap hoặc Google Maps để lấy lại tọa độ chính xác hơn.

```json
[
  {
    "station_id": "S01",
    "station_name": "Cong chinh",
    "location_type": "main_gate",
    "latitude": 20.9441,
    "longitude": 105.9439,
    "base_pm25": 38,
    "description": "Khu vuc cong chinh, PM2.5 tang vao gio cao diem"
  },
  {
    "station_id": "S02",
    "station_name": "Bai do xe",
    "location_type": "parking",
    "latitude": 20.9450,
    "longitude": 105.9435,
    "base_pm25": 42,
    "description": "Khu vuc bai do xe, anh huong boi xe ra vao"
  },
  {
    "station_id": "S03",
    "station_name": "Truc duong chinh",
    "location_type": "main_road",
    "latitude": 20.9445,
    "longitude": 105.9452,
    "base_pm25": 45,
    "description": "Tuyen duong chinh, co mat do giao thong cao"
  },
  {
    "station_id": "S04",
    "station_name": "Cong vien",
    "location_type": "park",
    "latitude": 20.9455,
    "longitude": 105.9458,
    "base_pm25": 28,
    "description": "Khu cong vien, PM2.5 thuong thap hon khu giao thong"
  },
  {
    "station_id": "S05",
    "station_name": "Khu the thao ngoai troi",
    "location_type": "sport_area",
    "latitude": 20.9437,
    "longitude": 105.9448,
    "base_pm25": 34,
    "description": "Khu the thao, dung cho khuyen nghi hoat dong ngoai troi"
  }
]
```

Tọa độ trung tâm bản đồ đề xuất:

```env
MAP_CENTER_LAT=20.9446
MAP_CENTER_LNG=105.9447
MAP_DEFAULT_ZOOM=16
```

---

## 4. Kiến trúc hệ thống

### 4.1. Sơ đồ tổng thể

```text
Open-Meteo Weather API
        ↓
Weather Collector
        ↓
Sensor Simulator → MQTT Broker → MQTT Consumer → FastAPI Backend → PostgreSQL
                                                           ↓
                                            Alert Engine + Forecast Service
                                                           ↓
                                                    AI Agent Tools
                                                           ↓
                                             React Leaflet Dashboard
                                                           ↓
                                                    HITL Approval
                                                           ↓
                              FastAPI → MQTT Command → Device Simulator
```

### 4.2. Thành phần chính

#### Sensor Simulator

- Python service.
- Đọc danh sách 5 trạm từ file JSON.
- Sinh PM2.5 theo:
  - base_pm25;
  - loại vị trí;
  - giờ cao điểm;
  - gió/mưa;
  - nhiễu nhỏ.
- Publish dữ liệu qua MQTT mỗi 10–30 giây.

#### MQTT Broker

- Dùng Eclipse Mosquitto.
- Chạy bằng Docker.

#### MQTT Consumer

- Subscribe topic dữ liệu cảm biến.
- Validate payload.
- Lưu raw data và clean data vào database.
- Cập nhật trạng thái trạm.

#### FastAPI Backend

- Cung cấp REST API cho frontend.
- Cung cấp tool functions cho AI Agent.
- Quản lý alerts, forecasts, approvals, devices.

#### PostgreSQL

- Lưu stations, measurements, weather_observations, alerts, users, approval_requests, devices, audit_logs.

#### Forecast Service

- MVP dùng baseline hoặc moving average.
- Sau đó có thể nâng cấp Linear Regression/Prophet.
- Đánh giá bằng MAE/RMSE.

#### AI Agent

- Không tự sinh số liệu.
- Chỉ gọi tool/backend API.
- Trả lời các câu hỏi về PM2.5 hiện tại, xu hướng, cảnh báo, khuyến nghị.

#### React Leaflet Dashboard

- Hiển thị bản đồ thật.
- Hiển thị 5 marker cảm biến.
- Marker đổi màu theo PM2.5.
- Popup hiển thị PM2.5, thời gian cập nhật, trạng thái.

#### HITL

- Agent tạo đề xuất.
- Quản lý phê duyệt hoặc từ chối.
- Nếu approved, backend mới gửi MQTT command tới thiết bị giả lập.

---

## 5. MQTT topic design

### Sensor measurements

```text
airguard/stations/{station_id}/measurements
```

Ví dụ:

```text
airguard/stations/S01/measurements
```

Payload:

```json
{
  "message_id": "MSG-S01-20260801-001",
  "station_id": "S01",
  "pm25": 68.4,
  "temperature": 32.1,
  "humidity": 72,
  "wind_speed": 1.8,
  "rainfall": 0,
  "timestamp": "2026-08-01T17:30:00+07:00",
  "source": "simulator"
}
```

### Station status

```text
airguard/stations/{station_id}/status
```

Payload:

```json
{
  "station_id": "S01",
  "status": "online",
  "timestamp": "2026-08-01T17:30:00+07:00"
}
```

### Device command

```text
airguard/devices/{device_id}/command
```

Payload:

```json
{
  "request_id": "REQ-001",
  "device_id": "FILTER-01",
  "action": "turn_on",
  "duration_minutes": 20,
  "approved_by": "manager_01",
  "reason": "PM2.5 exceeded threshold"
}
```

### Device status

```text
airguard/devices/{device_id}/status
```

Payload:

```json
{
  "device_id": "FILTER-01",
  "status": "running",
  "request_id": "REQ-001",
  "timestamp": "2026-08-01T17:31:00+07:00"
}
```

---

## 6. Database schema ban đầu

Tạo file: `backend/db/schema.sql`

```sql
CREATE TABLE IF NOT EXISTS stations (
    station_id VARCHAR(50) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    description TEXT,
    source VARCHAR(30) NOT NULL DEFAULT 'simulator',
    status VARCHAR(20) NOT NULL DEFAULT 'online',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS measurements (
    measurement_id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(100) UNIQUE NOT NULL,
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    measured_at TIMESTAMPTZ NOT NULL,
    pm25 DOUBLE PRECISION NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    wind_direction DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    source VARCHAR(30) NOT NULL DEFAULT 'simulator',
    quality_flag VARCHAR(20) NOT NULL DEFAULT 'valid',
    quality_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_measurements_station_time
ON measurements(station_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS weather_observations (
    weather_id BIGSERIAL PRIMARY KEY,
    area_id VARCHAR(50) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    wind_direction DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id UUID PRIMARY KEY,
    station_id VARCHAR(50) REFERENCES stations(station_id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    observed_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash TEXT,
    role VARCHAR(30) NOT NULL,
    full_name VARCHAR(150),
    sensitivity_group VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    station_id VARCHAR(50) REFERENCES stations(station_id),
    status VARCHAR(30) NOT NULL DEFAULT 'offline',
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approval_requests (
    request_id UUID PRIMARY KEY,
    request_type VARCHAR(50) NOT NULL,
    station_id VARCHAR(50) REFERENCES stations(station_id),
    device_id VARCHAR(50) REFERENCES devices(device_id),
    proposed_action VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_by VARCHAR(50) NOT NULL DEFAULT 'ai_agent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_by UUID REFERENCES users(user_id),
    reviewed_at TIMESTAMPTZ,
    review_note TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    actor_type VARCHAR(30) NOT NULL,
    actor_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 7. API contract ban đầu

Tạo file: `docs/api-contract.md`

### Stations

```http
GET /api/v1/stations
GET /api/v1/stations/{station_id}
GET /api/v1/stations/{station_id}/current
GET /api/v1/stations/{station_id}/history?hours=24
```

### Weather

```http
GET /api/v1/weather/current
```

### Alerts

```http
GET /api/v1/alerts
POST /api/v1/alerts/{alert_id}/resolve
```

### Forecast

```http
GET /api/v1/stations/{station_id}/forecast?hours=3
```

### AI Agent

```http
POST /api/v1/agent/chat
```

Request:

```json
{
  "user_id": "demo-user",
  "message": "Hien tai co nen chay bo o cong vien khong?"
}
```

Response:

```json
{
  "answer": "PM2.5 tai cong vien hien o muc trung binh. Neu ban thuoc nhom nhay cam, nen giam cuong do hoat dong ngoai troi.",
  "used_tools": ["get_current_pm25", "get_weather_context", "get_pm25_forecast"]
}
```

### HITL

```http
GET /api/v1/approvals
POST /api/v1/approvals/{request_id}/approve
POST /api/v1/approvals/{request_id}/reject
```

### Devices

```http
GET /api/v1/devices
GET /api/v1/devices/{device_id}/status
```

---

## 8. User stories

Tạo file: `docs/user-stories.md`

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-001 | Là cư dân, tôi muốn xem PM2.5 tại từng điểm trên bản đồ để biết khu vực nào nên tránh. | P0 | Bản đồ hiển thị ít nhất 5 marker, mỗi marker có PM2.5 hiện tại. |
| US-002 | Là cư dân, tôi muốn xem thời gian cập nhật gần nhất để biết dữ liệu có mới không. | P0 | Popup hoặc card hiển thị timestamp cập nhật. |
| US-003 | Là cư dân, tôi muốn xem lịch sử PM2.5 của một trạm để hiểu xu hướng. | P0 | Có API/history hoặc mock chart hiển thị dữ liệu theo thời gian. |
| US-004 | Là ban quản lý, tôi muốn biết cảm biến nào offline để kiểm tra dữ liệu. | P0 | Trạm offline được hiển thị trạng thái khác. |
| US-005 | Là ban quản lý, tôi muốn nhận cảnh báo khi PM2.5 vượt ngưỡng. | P0 | Khi PM2.5 vượt threshold, hệ thống tạo alert. |
| US-006 | Là người dùng nhạy cảm, tôi muốn nhận khuyến nghị nghiêm ngặt hơn người bình thường. | P1 | Câu trả lời Agent thay đổi theo sensitivity_group. |
| US-007 | Là người chạy bộ, tôi muốn biết có nên hoạt động ngoài trời trong 1–3 giờ tới không. | P1 | Agent dùng forecast để khuyến nghị. |
| US-008 | Là ban quản lý, tôi muốn phê duyệt cảnh báo diện rộng trước khi gửi. | P1 | Approval request có trạng thái pending/approved/rejected. |
| US-009 | Là ban quản lý, tôi muốn phê duyệt lệnh thiết bị giả lập trước khi thực thi. | P1 | Chỉ approved request mới publish MQTT command. |
| US-010 | Là nhóm phát triển, tôi muốn có audit log để truy vết hành động quan trọng. | P2 | Hệ thống lưu log khi tạo/phê duyệt/từ chối request. |

---

## 9. Backlog ban đầu

Tạo file: `docs/backlog.md`

### P0 — Trước coaching / Demo 1 foundation

| ID | Task | Owner | Output |
|---|---|---|---|
| T-001 | Cập nhật README và Project Charter summary | Team Lead | README.md |
| T-002 | Tạo repo structure | Team Lead | Folder structure |
| T-003 | Tạo file stations.json với 5 điểm cảm biến | Frontend/Data | `data/stations.json` |
| T-004 | Chạy Mosquitto bằng Docker Compose | Data/IoT | Broker chạy được |
| T-005 | Viết sensor simulator publish PM2.5 qua MQTT | Data/IoT | `simulators/sensor_simulator` |
| T-006 | Tạo FastAPI backend skeleton | Backend | `/health`, `/api/v1/stations` |
| T-007 | Tạo database schema SQL | Backend | `backend/db/schema.sql` |
| T-008 | Tạo React Leaflet map prototype | Frontend | Map hiển thị 5 marker mock |
| T-009 | Viết API contract | Backend | `docs/api-contract.md` |
| T-010 | Viết user stories | Team Lead | `docs/user-stories.md` |
| T-011 | Viết architecture doc | Team Lead/Backend | `docs/architecture.md` |
| T-012 | Thiết kế Agent tools | AI/ML | `docs/agent-tools.md` |

### P1 — Sau coaching / Demo 1 hoàn chỉnh

| ID | Task | Owner | Output |
|---|---|---|---|
| T-013 | MQTT Consumer lưu data vào PostgreSQL | Backend/Data | Data vào DB |
| T-014 | API current/history lấy dữ liệu thật từ DB | Backend | REST API |
| T-015 | Frontend gọi API thay mock data | Frontend | Map cập nhật data |
| T-016 | Alert rule PM2.5 vượt ngưỡng | Backend | Alerts |
| T-017 | Sensor offline detection | Backend/Data | Station status |
| T-018 | Docker Compose đầy đủ | Backend | App chạy multi-service |

### P2 — Demo 2

| ID | Task | Owner | Output |
|---|---|---|---|
| T-019 | Forecast Service baseline/moving average | AI/ML | Forecast API |
| T-020 | Tính MAE/RMSE trên dữ liệu test | AI/ML | Metrics report |
| T-021 | AI Agent gọi tool backend | AI/ML | Agent chat endpoint |
| T-022 | HITL approval workflow | Backend | Approvals API |
| T-023 | Device simulator nhận command MQTT | Data/IoT | Device status |
| T-024 | Manager dashboard approve/reject | Frontend | HITL UI |

---

## 10. Phân công nhóm 4 người

Tạo file: `docs/team-roles.md`

| Vai trò | Người phụ trách | Trách nhiệm |
|---|---|---|
| Team Lead / Backend | `[Tên]` | Quản lý tiến độ, FastAPI, PostgreSQL, API contract, tích hợp hệ thống, báo cáo mentor. |
| Data / IoT Engineer | `[Tên]` | MQTT Broker, Sensor Simulator, Device Simulator, Weather API, data validation. |
| AI / ML Engineer | `[Tên]` | Forecast Service, MAE/RMSE, Agent tools, prompt/tool-calling, recommendation rules. |
| Frontend / QA Engineer | `[Tên]` | React, Leaflet Map, marker UI, charts, HITL UI, test demo flow. |

Trước coaching, nếu chưa có tên, để placeholder nhưng phải có role rõ.

---

## 11. Agent tool design

Tạo file: `docs/agent-tools.md`

Agent không tự sinh dữ liệu. Agent chỉ gọi tool.

### Tools

```text
get_current_pm25(station_id)
get_station_history(station_id, hours)
get_weather_context()
get_pm25_forecast(station_id, hours)
get_active_alerts(station_id)
compare_stations()
get_user_profile(user_id)
create_warning_proposal(station_id, reason)
create_device_action_proposal(device_id, action, reason)
```

### Agent responsibilities

- Giải thích PM2.5 hiện tại.
- So sánh khu vực.
- Trả lời có nên hoạt động ngoài trời không.
- Dựa vào forecast để khuyến nghị.
- Tạo proposal khi cần cảnh báo diện rộng hoặc bật thiết bị.

### Agent constraints

- Không tự tạo số liệu PM2.5.
- Không tự gửi cảnh báo diện rộng.
- Không tự điều khiển thiết bị.
- Mọi hành động quan trọng phải qua HITL.
- Câu trả lời phải nêu nguồn dữ liệu và thời gian cập nhật nếu có.

---

## 12. Sensor simulator prototype

Tạo folder: `simulators/sensor_simulator/`

### `requirements.txt`

```txt
paho-mqtt==2.1.0
python-dotenv==1.0.1
```

### `sensor_simulator.py`

```python
import json
import os
import random
import time
from datetime import datetime, timezone, timedelta

import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL_SECONDS = int(os.getenv("SENSOR_INTERVAL_SECONDS", "10"))

VIETNAM_TZ = timezone(timedelta(hours=7))

STATIONS = [
    {"station_id": "S01", "station_name": "Cong chinh", "location_type": "main_gate", "base_pm25": 38},
    {"station_id": "S02", "station_name": "Bai do xe", "location_type": "parking", "base_pm25": 42},
    {"station_id": "S03", "station_name": "Truc duong chinh", "location_type": "main_road", "base_pm25": 45},
    {"station_id": "S04", "station_name": "Cong vien", "location_type": "park", "base_pm25": 28},
    {"station_id": "S05", "station_name": "Khu the thao", "location_type": "sport_area", "base_pm25": 34},
]


def is_rush_hour(now: datetime) -> bool:
    return 7 <= now.hour <= 9 or 16 <= now.hour <= 18


def location_factor(location_type: str) -> float:
    factors = {
        "main_gate": 8,
        "parking": 12,
        "main_road": 15,
        "park": -8,
        "sport_area": 0,
    }
    return factors.get(location_type, 0)


def simulate_pm25(station: dict) -> float:
    now = datetime.now(VIETNAM_TZ)
    base = station["base_pm25"]
    rush = 12 if is_rush_hour(now) else 0
    loc = location_factor(station["location_type"])

    # Mock weather effect. Later replace by real weather context.
    wind_speed = random.uniform(0.5, 4.5)
    rainfall = random.choice([0, 0, 0, 1])
    weather_effect = -1.5 * wind_speed - (8 if rainfall else 0)

    noise = random.gauss(0, 3)
    value = base + rush + loc + weather_effect + noise
    return round(max(1, value), 2)


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    print(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}")

    counter = 0
    try:
        while True:
            counter += 1
            now = datetime.now(VIETNAM_TZ).isoformat()

            for station in STATIONS:
                pm25 = simulate_pm25(station)
                topic = f"airguard/stations/{station['station_id']}/measurements"
                payload = {
                    "message_id": f"MSG-{station['station_id']}-{counter}",
                    "station_id": station["station_id"],
                    "pm25": pm25,
                    "temperature": round(random.uniform(28, 35), 1),
                    "humidity": random.randint(55, 85),
                    "wind_speed": round(random.uniform(0.5, 4.5), 1),
                    "rainfall": random.choice([0, 0, 0, 1]),
                    "timestamp": now,
                    "source": "simulator",
                }

                client.publish(topic, json.dumps(payload), qos=0)
                print(topic, payload)

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("Stopping simulator...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
```

---

## 13. Backend skeleton

Tạo folder: `backend/`

### `requirements.txt`

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.8.2
python-dotenv==1.0.1
psycopg2-binary==2.9.9
SQLAlchemy==2.0.32
```

### `app/main.py`

```python
from fastapi import FastAPI

app = FastAPI(title="AirGuard AI API", version="0.1.0")

STATIONS = [
    {
        "station_id": "S01",
        "station_name": "Cong chinh",
        "location_type": "main_gate",
        "latitude": 20.9441,
        "longitude": 105.9439,
        "pm25": 42.5,
        "status": "online",
    },
    {
        "station_id": "S02",
        "station_name": "Bai do xe",
        "location_type": "parking",
        "latitude": 20.9450,
        "longitude": 105.9435,
        "pm25": 55.2,
        "status": "online",
    },
    {
        "station_id": "S03",
        "station_name": "Truc duong chinh",
        "location_type": "main_road",
        "latitude": 20.9445,
        "longitude": 105.9452,
        "pm25": 66.1,
        "status": "online",
    },
    {
        "station_id": "S04",
        "station_name": "Cong vien",
        "location_type": "park",
        "latitude": 20.9455,
        "longitude": 105.9458,
        "pm25": 28.4,
        "status": "online",
    },
    {
        "station_id": "S05",
        "station_name": "Khu the thao",
        "location_type": "sport_area",
        "latitude": 20.9437,
        "longitude": 105.9448,
        "pm25": 35.9,
        "status": "online",
    },
]


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "airguard-api"}


@app.get("/api/v1/stations")
def get_stations():
    return {"items": STATIONS}


@app.get("/api/v1/stations/{station_id}/current")
def get_station_current(station_id: str):
    for station in STATIONS:
        if station["station_id"] == station_id:
            return station
    return {"error": "station_not_found"}
```

Run:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 14. Frontend React Leaflet skeleton

Tạo folder: `frontend/`

Cài:

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install leaflet react-leaflet
```

Trong `src/main.jsx` thêm:

```jsx
import "leaflet/dist/leaflet.css";
```

Tạo `src/App.jsx`:

```jsx
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const stations = [
  { station_id: "S01", station_name: "Cong chinh", latitude: 20.9441, longitude: 105.9439, pm25: 42.5 },
  { station_id: "S02", station_name: "Bai do xe", latitude: 20.9450, longitude: 105.9435, pm25: 55.2 },
  { station_id: "S03", station_name: "Truc duong chinh", latitude: 20.9445, longitude: 105.9452, pm25: 66.1 },
  { station_id: "S04", station_name: "Cong vien", latitude: 20.9455, longitude: 105.9458, pm25: 28.4 },
  { station_id: "S05", station_name: "Khu the thao", latitude: 20.9437, longitude: 105.9448, pm25: 35.9 },
];

function getPm25Level(pm25) {
  if (pm25 <= 25) return "Good";
  if (pm25 <= 50) return "Moderate";
  if (pm25 <= 100) return "Unhealthy";
  return "Very Unhealthy";
}

export default function App() {
  return (
    <div style={{ padding: 16 }}>
      <h1>AirGuard AI Dashboard</h1>
      <p>Prototype bản đồ PM2.5 với 5 điểm cảm biến giả lập.</p>

      <MapContainer
        center={[20.9446, 105.9447]}
        zoom={16}
        style={{ height: "600px", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {stations.map((station) => (
          <Marker
            key={station.station_id}
            position={[station.latitude, station.longitude]}
          >
            <Popup>
              <strong>{station.station_name}</strong>
              <br />
              PM2.5: {station.pm25} µg/m³
              <br />
              Level: {getPm25Level(station.pm25)}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
```

---

## 15. Docker Compose tối thiểu

Tạo file `docker-compose.yml` ở root.

```yaml
services:
  mqtt:
    image: eclipse-mosquitto:2
    container_name: airguard-mqtt
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mqtt/mosquitto.conf:/mosquitto/config/mosquitto.conf

  postgres:
    image: postgres:16
    container_name: airguard-postgres
    environment:
      POSTGRES_USER: airguard
      POSTGRES_PASSWORD: airguard
      POSTGRES_DB: airguard
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/schema.sql:/docker-entrypoint-initdb.d/schema.sql

volumes:
  postgres_data:
```

Tạo file `mqtt/mosquitto.conf`:

```conf
listener 1883
allow_anonymous true

listener 9001
protocol websockets
allow_anonymous true
```

Run:

```bash
docker compose up -d
```

---

## 16. README.md cần tạo ở root

README nên có các mục:

```md
# AirGuard AI

## 1. Project Overview
## 2. Problem
## 3. Proposed Solution
## 4. MVP Scope
## 5. System Architecture
## 6. Tech Stack
## 7. Data Model
## 8. MQTT Topics
## 9. User Stories
## 10. Backlog
## 11. How to Run
## 12. Team Roles
## 13. Mentor Questions
```

Phần `How to Run` tối thiểu:

```bash
# Start MQTT and PostgreSQL
docker compose up -d

# Run sensor simulator
cd simulators/sensor_simulator
pip install -r requirements.txt
python sensor_simulator.py

# Run backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run frontend
cd frontend
npm install
npm run dev
```

---

## 17. Những file cần có trước khi push Git

Repository cần có ít nhất:

```text
airguard-ai/
├── README.md
├── docker-compose.yml
├── .env.example
├── data/
│   └── stations.json
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── backlog.md
│   ├── user-stories.md
│   ├── team-roles.md
│   └── agent-tools.md
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   └── main.py
│   └── db/
│       └── schema.sql
├── frontend/
│   └── README.md hoặc Vite React app
├── mqtt/
│   └── mosquitto.conf
└── simulators/
    └── sensor_simulator/
        ├── requirements.txt
        └── sensor_simulator.py
```

---

## 18. Git commands

```bash
git init
git add .
git commit -m "initial airguard ai project structure"
git branch -M main
git remote add origin <GITHUB_REPO_URL>
git push -u origin main
```

Nếu repo đã tồn tại:

```bash
git status
git add .
git commit -m "add airguard project charter architecture and prototype"
git push origin main
```

---

## 19. Definition of Done cho lần push đầu tiên

Một lần push đầu tiên được xem là đủ nếu có:

- README mô tả được project.
- Docs có architecture, user stories, backlog, data model, agent tools.
- Có schema SQL.
- Có file 5 điểm cảm biến.
- Có docker-compose cho MQTT và PostgreSQL.
- Có sensor simulator publish MQTT.
- Có backend skeleton chạy `/health`.
- Có frontend map prototype hoặc README hướng dẫn tạo frontend.
- Không có secret/API key thật trong repo.

---

## 20. Ghi chú cho coding agent

Ưu tiên tạo file và cấu trúc trước. Không cần làm production-ready. Không thêm tính năng ngoài phạm vi. Không đưa API key thật vào repo. Mọi dữ liệu cảm biến đều phải ghi rõ là `simulator`. Phần PM2.5 ngoài trời là trọng tâm, các chỉ số khác chỉ để mở rộng sau.

