# AirGuard AI

> AI Agent giám sát chất lượng không khí ngoài trời, hỗ trợ theo dõi PM2.5, phân tích rủi ro, đưa ra khuyến nghị cá nhân hóa và tạo đề xuất cảnh báo có Human-in-the-Loop.

---

# 1. Mục tiêu của README

README này là **nguồn tham chiếu chính của dự án** dành cho Frontend, Backend, AI Agent và Data/IoT.

Mục tiêu:

- Chốt phạm vi MVP trước khi code.
- Chốt toàn bộ API giữa Frontend và Backend.
- Chốt toàn bộ Agent Tool trước khi triển khai.
- Chốt request, response, error và data schema.
- Tạo codebase skeleton tối thiểu để các thành viên làm song song.
- Tránh FE và BE tự đặt field khác nhau.
- Tránh Agent gọi tool chưa tồn tại.
- Có metrics và test plan rõ ràng.
- Có Definition of Ready và Definition of Done.

## Nguyên tắc bắt buộc

1. **Contract trước, code sau.**
2. API chưa có logic thật vẫn phải có mock response đúng schema.
3. Không đổi tên field API sau khi Frontend đã tích hợp nếu chưa thống nhất.
4. Agent chỉ được gọi tool đã định nghĩa.
5. Mỗi tool phải có input, output, error và test case.
6. Frontend không truy cập database hoặc MQTT trực tiếp.
7. Agent không đọc database trực tiếp.
8. Agent không được tự bịa số liệu.
9. Alert threshold do rule engine quyết định, không phải LLM.
10. Agent không được tự approve hoặc reject warning proposal.

---

# 2. Tổng quan dự án

## 2.1. Bài toán

Trong khu đô thị hoặc campus, dữ liệu chất lượng không khí thường:

- Phân tán ở nhiều nguồn.
- Khó theo dõi theo vị trí.
- Khó hiểu với người dùng phổ thông.
- Không đưa ra được khuyến nghị hành động rõ ràng.
- Thiếu luồng kiểm soát cảnh báo bởi con người.

Người dùng cần biết:

- PM2.5 hiện tại tại từng khu vực.
- Khu vực nào ô nhiễm nhất.
- Có nên chạy bộ hoặc hoạt động ngoài trời không.
- Người nhạy cảm nên tránh khu vực nào.
- Chất lượng không khí có xu hướng tăng hay giảm.
- Hiện có cảnh báo nào.

Ban quản lý cần:

- Theo dõi nhiều trạm đo trên một dashboard.
- Phát hiện PM2.5 cao, sensor offline hoặc dữ liệu stale.
- Xem đề xuất cảnh báo do Agent tạo.
- Approve hoặc reject đề xuất.
- Lưu audit log.

## 2.2. Giải pháp

AirGuard AI gồm:

1. Sensor Simulator tạo dữ liệu PM2.5.
2. MQTT Broker nhận dữ liệu.
3. Backend FastAPI validate và lưu dữ liệu.
4. PostgreSQL lưu station, measurement, alert, proposal, user và trace.
5. Frontend React hiển thị dashboard và giao diện quản lý.
6. AI Agent gọi tool để lấy dữ liệu và trả lời.
7. Alert Engine tạo cảnh báo theo rule.
8. Warning Proposal đi qua Human-in-the-Loop.

---

# 3. Phạm vi MVP

## 3.1. Trong phạm vi

- 5 sensor PM2.5 giả lập.
- MQTT message publishing.
- FastAPI Backend.
- PostgreSQL.
- Dashboard bản đồ.
- Chi tiết station.
- Lịch sử PM2.5.
- Active alerts.
- Login cơ bản.
- AI Agent chat.
- Tool calling.
- Recommendation cho 3 nhóm người dùng.
- Warning proposal.
- Manager approve/reject.
- Agent trace.
- Audit log.
- Forecast baseline 1–3 giờ nếu đủ thời gian.

## 3.2. Ngoài phạm vi MVP

- Sensor vật lý thật.
- Deep learning/LSTM nâng cao.
- Mobile app.
- Điều khiển thiết bị thật.
- Multi-agent network tự trị.
- Agent tự approve/reject.
- Production scaling lớn.
- Vector database nếu chưa thực sự cần.

---

# 4. Vai trò người dùng

## 4.1. Resident/User

Có thể:

- Login.
- Xem dashboard.
- Xem station.
- Xem lịch sử.
- Hỏi AI Agent.
- Xem cảnh báo public.
- Xem hoặc cập nhật profile.

Không thể:

- Approve/reject proposal.
- Thay đổi threshold.
- Quản lý station.
- Xem audit log toàn hệ thống.

## 4.2. Manager

Có thể:

- Thực hiện quyền của User.
- Xem warning proposal.
- Approve/reject proposal.
- Nhập review note.
- Xem audit log liên quan.

## 4.3. Admin

Chỉ triển khai nếu được chốt trong MVP.

Có thể:

- Quản lý user.
- Quản lý station metadata.
- Quản lý threshold.
- Xem toàn bộ audit log.
- Quản lý quyền.

---

# 5. Kiến trúc hệ thống

```text
Sensor Simulator
      |
      v
MQTT Broker
      |
      v
Backend MQTT Consumer
      |
      v
Validation + Data Quality
      |
      v
PostgreSQL
      |
      +----------------------------+
      |                            |
      v                            v
REST API                      Alert Engine
      |                            |
      v                            v
Frontend                     Active Alerts
      |
      v
AI Agent API
      |
      v
Tool Calling
      |
      +--> Station API
      +--> Measurement API
      +--> Weather API
      +--> Forecast Service
      +--> Alert API
      +--> User API
      +--> Proposal API
```

## Ràng buộc kiến trúc

- Frontend không kết nối MQTT.
- Frontend không truy cập PostgreSQL.
- Agent không truy cập database trực tiếp.
- Mọi số liệu Agent sử dụng phải đến từ tool.
- Alert Engine sử dụng rule deterministic.
- Warning Proposal phải có trạng thái `pending` trước khi manager xử lý.

---

# 6. Công nghệ

## Frontend

- React.
- Vite.
- JavaScript hoặc TypeScript.
- React Router.
- React Leaflet.
- OpenStreetMap.
- Axios hoặc Fetch.
- Recharts hoặc Chart.js.

## Backend

- Python.
- FastAPI.
- Pydantic.
- PostgreSQL.
- psycopg2 hoặc SQLAlchemy.
- Alembic nếu dùng migration.
- paho-mqtt.

## AI Agent

- Python.
- LangGraph hoặc orchestration tương đương.
- Tool calling.
- Structured output.
- Trace logging.
- Guardrails.

## Data/IoT

- Mosquitto.
- Sensor Simulator.
- MQTT JSON payload.
- Weather API.
- Forecast baseline.

---

# 7. Codebase skeleton tối thiểu

"Mục này cứ làm theo kiến trúc thư mục hiện tại. Cần thiết bạn sẽ sắp xếp lại thư mục sau"

```text
airguard-ai/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── stations.py
│   │   │   ├── measurements.py
│   │   │   ├── alerts.py
│   │   │   ├── proposals.py
│   │   │   ├── users.py
│   │   │   └── agent.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── station_service.py
│   │   │   ├── measurement_service.py
│   │   │   ├── alert_engine.py
│   │   │   ├── proposal_service.py
│   │   │   ├── audit_service.py
│   │   │   └── mqtt_consumer.py
│   │   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── pages/
│       ├── components/
│       ├── services/
│       │   ├── apiClient.js
│       │   ├── authApi.js
│       │   ├── stationApi.js
│       │   ├── alertApi.js
│       │   ├── proposalApi.js
│       │   └── agentApi.js
│       └── styles/
│
├── agent/
│   ├── graph.py
│   ├── state.py
│   ├── prompts.py
│   ├── guardrails.py
│   ├── intents.py
│   ├── tools/
│   │   ├── station_tools.py
│   │   ├── weather_tools.py
│   │   ├── forecast_tools.py
│   │   ├── alert_tools.py
│   │   ├── user_tools.py
│   │   ├── proposal_tools.py
│   │   └── trace_tools.py
│   └── tests/
│
├── simulators/
│   ├── sensor_simulator.py
│   ├── scenario_engine.py
│   ├── stations.json
│   └── README.md
│
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── migrations/
│
└── docs/
    ├── API_CONVENTION.md
    ├── AGENT_TOOLS.md
    ├── AGENT_DESIGN.md
    ├── DATA_CONTRACT.md
    ├── METRICS.md
    ├── TEST_PLAN.md
    └── UI_FLOW.md
```

---

# 8. Quy chuẩn API FE–BE

## 8.1. Base URL

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Frontend không hard-code URL trực tiếp trong component.

## 8.2. Response thành công

```json
{
  "success": true,
  "data": {},
  "message": "OK",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

## 8.3. Response lỗi

```json
{
  "success": false,
  "error": {
    "code": "STATION_NOT_FOUND",
    "message": "Không tìm thấy trạm",
    "details": {
      "station_id": "S99"
    }
  },
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

## 8.4. HTTP status code

| Status | Ý nghĩa          |
| ------ | ---------------- |
| 200    | Thành công       |
| 201    | Tạo mới          |
| 400    | Request sai      |
| 401    | Chưa đăng nhập   |
| 403    | Không có quyền   |
| 404    | Không tìm thấy   |
| 409    | Conflict         |
| 422    | Validation error |
| 500    | Lỗi server       |

## 8.5. Quy chuẩn field

- JSON dùng `snake_case`.
- Timestamp dùng ISO 8601.
- PM2.5 phải là number.
- Không trả số dưới dạng string.
- ID phải thống nhất.
- Mọi dữ liệu realtime phải có `measured_at`.
- Mọi response phải có `timestamp`.

---

# 9. Danh sách API bắt buộc phải define trước

## 9.1. Health Check

```http
GET /api/v1/health
```

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "mqtt": "connected"
  },
  "message": "Service is healthy",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.2. Login

```http
POST /api/v1/auth/login
```

### Request

```json
{
  "email": "manager@airguard.local",
  "password": "example_password"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "user_id": "U001",
      "full_name": "Manager Demo",
      "email": "manager@airguard.local",
      "role": "manager",
      "user_group": "normal"
    }
  },
  "message": "Đăng nhập thành công",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

### Error

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email hoặc mật khẩu không đúng",
    "details": null
  },
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.3. Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

```json
{
  "success": true,
  "data": {
    "user_id": "U001",
    "full_name": "Manager Demo",
    "email": "manager@airguard.local",
    "role": "manager",
    "user_group": "normal"
  },
  "message": "Current user fetched",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.4. Logout

```http
POST /api/v1/auth/logout
```

```json
{
  "success": true,
  "data": null,
  "message": "Đăng xuất thành công",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.5. Get Stations

```http
GET /api/v1/stations
```

```json
{
  "success": true,
  "data": [
    {
      "station_id": "S01",
      "station_name": "Cổng chính",
      "latitude": 21.0001,
      "longitude": 105.9442,
      "location_type": "gate",
      "status": "online",
      "latest_pm25": 38.2,
      "measured_at": "2026-08-06T18:59:30+07:00"
    }
  ],
  "message": "Stations fetched",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.6. Get Station Detail

```http
GET /api/v1/stations/{station_id}
```

```json
{
  "success": true,
  "data": {
    "station_id": "S03",
    "station_name": "Trục đường chính",
    "latitude": 21.0001,
    "longitude": 105.9442,
    "location_type": "road",
    "status": "online",
    "description": "Điểm đo gần trục giao thông chính"
  },
  "message": "Station fetched",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.7. Current PM2.5

```http
GET /api/v1/stations/{station_id}/current
```

```json
{
  "success": true,
  "data": {
    "station_id": "S03",
    "station_name": "Trục đường chính",
    "pm25": 78.4,
    "unit": "ug/m3",
    "status": "online",
    "quality_flag": "valid",
    "source": "sensor_simulator",
    "measured_at": "2026-08-06T18:59:30+07:00"
  },
  "message": "Current PM2.5 fetched",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.8. Station History

```http
GET /api/v1/stations/{station_id}/history?hours=24
```

```json
{
  "success": true,
  "data": {
    "station_id": "S03",
    "from": "2026-08-05T19:00:00+07:00",
    "to": "2026-08-06T19:00:00+07:00",
    "measurements": [
      {
        "pm25": 55.2,
        "quality_flag": "valid",
        "measured_at": "2026-08-06T18:00:00+07:00"
      }
    ]
  },
  "message": "Station history fetched",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.9. Compare Stations

```http
POST /api/v1/stations/compare
```

```json
{
  "station_ids": ["S03", "S04", "S05"]
}
```

```json
{
  "success": true,
  "data": {
    "ranking": [
      {
        "rank": 1,
        "station_id": "S03",
        "station_name": "Trục đường chính",
        "pm25": 78.4,
        "measured_at": "2026-08-06T18:59:30+07:00"
      }
    ],
    "best_station_id": "S04",
    "worst_station_id": "S03"
  },
  "message": "Stations compared",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.10. Active Alerts

```http
GET /api/v1/alerts/active
```

```json
{
  "success": true,
  "data": [
    {
      "alert_id": "A001",
      "station_id": "S03",
      "type": "pm25_high",
      "severity": "high",
      "observed_value": 78.4,
      "threshold": 75.0,
      "status": "active",
      "created_at": "2026-08-06T18:55:00+07:00"
    }
  ],
  "message": "Active alerts fetched",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.11. Agent Chat

```http
POST /api/v1/agent/chat
Authorization: Bearer <token>
```

### Request

```json
{
  "conversation_id": "C001",
  "message": "Khu nào đang ô nhiễm nhất?"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "conversation_id": "C001",
    "answer": "S03 - Trục đường chính đang có PM2.5 cao nhất với 78.4 ug/m3.",
    "intent": "compare_stations",
    "tools_used": ["compare_stations"],
    "evidence": [
      {
        "station_id": "S03",
        "pm25": 78.4,
        "unit": "ug/m3",
        "source": "sensor_simulator",
        "measured_at": "2026-08-06T18:59:30+07:00"
      }
    ],
    "recommendation": "Hạn chế hoạt động ngoài trời tại S03.",
    "proposal": null,
    "trace_id": "T001"
  },
  "message": "Agent response generated",
  "timestamp": "2026-08-06T19:00:02+07:00"
}
```

---

## 9.12. Get Proposals

```http
GET /api/v1/proposals?status=pending
```

```json
{
  "success": true,
  "data": [
    {
      "proposal_id": "P001",
      "alert_id": "A001",
      "station_id": "S03",
      "status": "pending",
      "reason": "PM2.5 vượt ngưỡng",
      "created_by": "agent",
      "created_at": "2026-08-06T19:00:00+07:00"
    }
  ],
  "message": "Proposals fetched",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

---

## 9.13. Create Proposal

```http
POST /api/v1/proposals
```

```json
{
  "alert_id": "A001",
  "station_id": "S03",
  "reason": "PM2.5 vượt ngưỡng trong nhiều lần đo liên tiếp",
  "proposed_message": "Hạn chế hoạt động ngoài trời tại S03.",
  "evidence": [
    {
      "station_id": "S03",
      "pm25": 78.4,
      "source": "sensor_simulator",
      "measured_at": "2026-08-06T18:59:30+07:00"
    }
  ]
}
```

```json
{
  "success": true,
  "data": {
    "proposal_id": "P001",
    "status": "pending",
    "created_by": "agent",
    "created_at": "2026-08-06T19:00:05+07:00"
  },
  "message": "Warning proposal created",
  "timestamp": "2026-08-06T19:00:05+07:00"
}
```

---

## 9.14. Approve Proposal

```http
PATCH /api/v1/proposals/{proposal_id}/approve
```

```json
{
  "review_note": "Đã kiểm tra dữ liệu và đồng ý."
}
```

```json
{
  "success": true,
  "data": {
    "proposal_id": "P001",
    "status": "approved",
    "reviewed_by": "U001",
    "reviewed_at": "2026-08-06T19:05:00+07:00"
  },
  "message": "Proposal approved",
  "timestamp": "2026-08-06T19:05:00+07:00"
}
```

---

## 9.15. Reject Proposal

```http
PATCH /api/v1/proposals/{proposal_id}/reject
```

```json
{
  "review_note": "Dữ liệu chưa đủ mới."
}
```

```json
{
  "success": true,
  "data": {
    "proposal_id": "P001",
    "status": "rejected",
    "reviewed_by": "U001",
    "reviewed_at": "2026-08-06T19:05:00+07:00"
  },
  "message": "Proposal rejected",
  "timestamp": "2026-08-06T19:05:00+07:00"
}
```

---

# 10. API phải code trước

Backend cần tạo skeleton cho:

```text
GET    /api/v1/health
POST   /api/v1/auth/login
GET    /api/v1/auth/me
POST   /api/v1/auth/logout
GET    /api/v1/stations
GET    /api/v1/stations/{station_id}
GET    /api/v1/stations/{station_id}/current
GET    /api/v1/stations/{station_id}/history
POST   /api/v1/stations/compare
GET    /api/v1/alerts/active
POST   /api/v1/agent/chat
GET    /api/v1/proposals
POST   /api/v1/proposals
PATCH  /api/v1/proposals/{proposal_id}/approve
PATCH  /api/v1/proposals/{proposal_id}/reject
```

Ban đầu có thể trả mock data nhưng phải đúng schema.

---

# 11. Agent Definition

## 11.1. Supervisor/Router Agent

### Nhiệm vụ

- Nhận message.
- Xác định intent.
- Resolve station.
- Chọn tool.
- Điều phối các bước.
- Không tự tạo số liệu.

### Input

```json
{
  "user_id": "U001",
  "conversation_id": "C001",
  "message": "Khu nào đang ô nhiễm nhất?"
}
```

### Output nội bộ

```json
{
  "intent": "compare_stations",
  "resolved_station_ids": ["S01", "S02", "S03", "S04", "S05"],
  "selected_tools": ["compare_stations"]
}
```

## 11.2. Sensor Data Agent

### Nhiệm vụ

- Lấy PM2.5 hiện tại.
- Lấy lịch sử.
- So sánh station.

### Tool

- `get_current_pm25`
- `get_station_history`
- `compare_stations`

## 11.3. Weather Context Agent

### Nhiệm vụ

Lấy dữ liệu thời tiết hỗ trợ phân tích.

### Tool

- `get_weather_context`

## 11.4. Forecast Agent

### Nhiệm vụ

Dự báo PM2.5 1–3 giờ.

### Tool

- `get_pm25_forecast`

### Guardrail

- Không khẳng định chắc chắn.
- Phải trả model name.
- Phải trả generated time.
- Thiếu dữ liệu phải trả lỗi.

## 11.5. Risk Assessment Agent

### Input

- Current PM2.5.
- History.
- Forecast.
- Weather.
- User profile.
- Active alerts.

### Output

```json
{
  "risk_level": "high",
  "reasons": ["PM2.5 hiện tại cao", "Xu hướng tiếp tục tăng"],
  "affected_groups": ["sensitive", "outdoor_sport"]
}
```

## 11.6. Recommendation Agent

### Output

```json
{
  "recommendation": "Nên hoãn chạy bộ ngoài trời tại S05 trong 1–2 giờ.",
  "confidence": "medium",
  "basis": ["current_pm25", "forecast", "user_profile"]
}
```

## 11.7. Warning Proposal Agent

### Chỉ tạo proposal khi

- Có active alert.
- Sensor online.
- Data valid.
- Data không stale.
- Chưa có proposal pending trùng.
- Có evidence.

### Không được

- Approve.
- Reject.
- Phát hành cảnh báo trực tiếp.

## 11.8. Response Agent

Câu trả lời phải có:

- Số liệu.
- Đơn vị.
- Station.
- Timestamp.
- Source.
- Evidence.
- Recommendation.
- Confidence nếu dùng forecast.

## 11.9. Trace/Audit Agent

Lưu:

- Message.
- Intent.
- Tool.
- Tool input.
- Tool output.
- Error.
- Latency.
- Final answer.
- Proposal ID.

Không lưu:

- Password.
- API key.
- JWT raw token.

---

# 12. Agent Tool Contract

## 12.1. `get_current_pm25`

### Input

```json
{
  "station_id": "S03"
}
```

### Output

```json
{
  "station_id": "S03",
  "station_name": "Trục đường chính",
  "pm25": 78.4,
  "unit": "ug/m3",
  "status": "online",
  "quality_flag": "valid",
  "source": "sensor_simulator",
  "measured_at": "2026-08-06T18:59:30+07:00"
}
```

## 12.2. `get_station_history`

```json
{
  "station_id": "S03",
  "hours": 24
}
```

```json
{
  "station_id": "S03",
  "measurements": [
    {
      "pm25": 55.2,
      "measured_at": "2026-08-06T18:00:00+07:00"
    }
  ],
  "count": 24
}
```

## 12.3. `compare_stations`

```json
{
  "station_ids": ["S03", "S04", "S05"]
}
```

```json
{
  "ranking": [
    {
      "rank": 1,
      "station_id": "S03",
      "pm25": 78.4,
      "measured_at": "2026-08-06T18:59:30+07:00"
    }
  ],
  "best_station_id": "S04",
  "worst_station_id": "S03",
  "comparison_valid": true
}
```

## 12.4. `get_weather_context`

```json
{
  "location": "VinUni"
}
```

```json
{
  "temperature": 32.0,
  "humidity": 68.0,
  "wind_speed": 1.5,
  "rainfall": 0.0,
  "condition": "cloudy",
  "source": "weather_api",
  "observed_at": "2026-08-06T19:00:00+07:00"
}
```

## 12.5. `get_pm25_forecast`

```json
{
  "station_id": "S05",
  "hours": 3
}
```

```json
{
  "station_id": "S05",
  "forecast": [
    {
      "target_time": "2026-08-06T20:00:00+07:00",
      "predicted_pm25": 45.2
    }
  ],
  "model_name": "moving_average_baseline",
  "generated_at": "2026-08-06T19:00:00+07:00",
  "confidence": "medium"
}
```

## 12.6. `get_active_alerts`

```json
{
  "station_id": "S03"
}
```

```json
{
  "alerts": [
    {
      "alert_id": "A001",
      "type": "pm25_high",
      "severity": "high",
      "status": "active"
    }
  ]
}
```

## 12.7. `get_user_profile`

```json
{
  "user_id": "U001"
}
```

```json
{
  "user_id": "U001",
  "role": "resident",
  "user_group": "outdoor_sport"
}
```

## 12.8. `create_warning_proposal`

```json
{
  "alert_id": "A001",
  "station_id": "S03",
  "reason": "PM2.5 vượt ngưỡng",
  "evidence": [
    {
      "pm25": 78.4,
      "measured_at": "2026-08-06T18:59:30+07:00"
    }
  ],
  "proposed_message": "Hạn chế hoạt động ngoài trời tại S03."
}
```

```json
{
  "proposal_id": "P001",
  "status": "pending",
  "created_at": "2026-08-06T19:00:05+07:00"
}
```

## 12.9. `save_agent_trace`

```json
{
  "conversation_id": "C001",
  "user_id": "U001",
  "message": "Khu nào đang ô nhiễm nhất?",
  "intent": "compare_stations",
  "tools_used": ["compare_stations"],
  "tool_inputs": [],
  "tool_outputs": [],
  "final_answer": "S03 đang có PM2.5 cao nhất.",
  "latency_ms": 1820
}
```

```json
{
  "trace_id": "T001",
  "status": "saved"
}
```

---

# 13. Data Definition

## Station

```json
{
  "station_id": "S03",
  "station_name": "Trục đường chính",
  "latitude": 21.0001,
  "longitude": 105.9442,
  "location_type": "road",
  "status": "online"
}
```

## Measurement

```json
{
  "measurement_id": "M001",
  "station_id": "S03",
  "pm25": 78.4,
  "unit": "ug/m3",
  "quality_flag": "valid",
  "source": "sensor_simulator",
  "scenario": "high_pm25",
  "measured_at": "2026-08-06T18:59:30+07:00",
  "received_at": "2026-08-06T18:59:31+07:00"
}
```

## Alert

```json
{
  "alert_id": "A001",
  "station_id": "S03",
  "type": "pm25_high",
  "severity": "high",
  "observed_value": 78.4,
  "threshold": 75.0,
  "status": "active",
  "created_at": "2026-08-06T18:55:00+07:00"
}
```

## Proposal

```json
{
  "proposal_id": "P001",
  "alert_id": "A001",
  "station_id": "S03",
  "status": "pending",
  "reason": "PM2.5 vượt ngưỡng",
  "proposed_message": "Hạn chế hoạt động ngoài trời",
  "created_by": "agent",
  "created_at": "2026-08-06T19:00:00+07:00"
}
```

## User

```json
{
  "user_id": "U001",
  "full_name": "Demo User",
  "email": "user@airguard.local",
  "role": "resident",
  "user_group": "outdoor_sport"
}
```

---

# 14. Mô phỏng dữ liệu

## 14.1. 5 station

- S01 — Cổng chính.
- S02 — Bãi đỗ xe.
- S03 — Trục đường chính.
- S04 — Công viên.
- S05 — Khu thể thao ngoài trời.

## 14.2. Công thức mô phỏng

```text
PM2.5 =
base_value_by_station
+ rush_hour_effect
+ weather_effect
+ scenario_effect
+ small_noise
```

## 14.3. Scenario

- `normal`
- `high_pm25`
- `sudden_spike`
- `sensor_offline`
- `stale_data`
- `invalid_data`
- `rain_cleanup`

## 14.4. MQTT payload

```json
{
  "station_id": "S03",
  "pm25": 78.4,
  "unit": "ug/m3",
  "status": "online",
  "quality_flag": "valid",
  "scenario": "high_pm25",
  "measured_at": "2026-08-06T18:59:30+07:00"
}
```

Topic:

```text
airguard/sensors/S03/measurements
```

---

# 15. Data Quality Rules

Backend phải kiểm tra:

- `station_id` tồn tại.
- `pm25` không null.
- `pm25 >= 0`.
- `measured_at` hợp lệ.
- Không chấp nhận timestamp quá xa trong tương lai.
- Dữ liệu stale phải được đánh dấu.
- Duplicate message phải được xử lý.
- Sensor offline nếu không gửi dữ liệu đủ lâu.

Cấu hình MVP đề xuất:

```text
stale_after_minutes = 10
offline_after_minutes = 15
```

Các giá trị này cần nhóm hoặc mentor xác nhận.

---

# 16. Metrics

## 16.1. Agent Metrics

| Metric                  | Cách đo                            | Mục tiêu       |
| ----------------------- | ---------------------------------- | -------------- |
| Intent Accuracy         | Intent đúng / tổng test            | >= 80%         |
| Tool Selection Accuracy | Tool đúng / tổng test              | >= 80%         |
| Tool Call Success Rate  | Tool thành công / tổng call        | >= 90%         |
| Evidence Coverage       | Câu có evidence / câu cần evidence | >= 90%         |
| Hallucination Rate      | Câu bịa số / tổng câu              | 0%             |
| Trace Logging Rate      | Trace lưu / tổng lượt              | 100%           |
| Response Latency        | Thời gian phản hồi                 | < 5 giây local |
| Proposal Safety         | Proposal từ stale/invalid/offline  | 0 case         |

## 16.2. Backend Metrics

| Metric                       | Mục tiêu            |
| ---------------------------- | ------------------- |
| API success rate             | >= 95%              |
| P95 response time local      | < 1 giây            |
| Validation coverage          | 100% endpoint chính |
| Unauthorized request blocked | 100%                |
| Swagger schema coverage      | 100% API chính      |

## 16.3. Frontend Metrics

| Metric                    | Mục tiêu         |
| ------------------------- | ---------------- |
| Station hiển thị          | 5/5              |
| White screen/crash        | 0                |
| Loading/error/empty state | 100% màn gọi API |
| API integration success   | >= 90%           |
| Dashboard render success  | 100% demo        |

## 16.4. Data/MQTT Metrics

| Metric                 | Mục tiêu               |
| ---------------------- | ---------------------- |
| Sensor coverage        | 5/5                    |
| MQTT delivery          | >= 95%                 |
| Invalid data rejection | 100%                   |
| Timestamp completeness | 100%                   |
| Scenario coverage      | >= 6                   |
| Duplicate handling     | Không tạo record trùng |

## 16.5. Alert/HITL Metrics

| Metric                    | Mục tiêu        |
| ------------------------- | --------------- |
| High PM2.5 detection      | >= 90% scenario |
| Duplicate alert           | 0 trong demo    |
| Approve/reject completion | 100%            |
| Audit log coverage        | 100%            |
| Agent tự approve/reject   | 0%              |

---

# 17. Cách đánh giá Agent

Chuẩn bị ít nhất 10 test case.

| ID    | Câu hỏi                            | Intent                 | Tool                                   |
| ----- | ---------------------------------- | ---------------------- | -------------------------------------- |
| AG-01 | PM2.5 ở S03 hiện tại là bao nhiêu? | current_pm25           | get_current_pm25                       |
| AG-02 | PM2.5 S03 có đang tăng không?      | station_history        | get_station_history                    |
| AG-03 | Khu nào ô nhiễm nhất?              | compare_stations       | compare_stations                       |
| AG-04 | So sánh S03 và S04                 | compare_stations       | compare_stations                       |
| AG-05 | Tôi có nên chạy bộ ở S05 không?    | outdoor_recommendation | current + weather + forecast + profile |
| AG-06 | Hiện có cảnh báo nào?              | active_alerts          | get_active_alerts                      |
| AG-07 | Vì sao S03 bị cảnh báo?            | alert_explanation      | active_alerts + history                |
| AG-08 | 3 giờ tới PM2.5 S05 thế nào?       | forecast_pm25          | get_pm25_forecast                      |
| AG-09 | Có cần tạo cảnh báo không?         | proposal_creation      | alerts + proposal                      |
| AG-10 | Hôm nay chứng khoán thế nào?       | out_of_scope           | không gọi tool môi trường              |

Mỗi test phải chấm:

- Intent đúng/sai.
- Tool đúng/sai.
- Tool input đúng/sai.
- Output có evidence không.
- Có timestamp không.
- Có hallucination không.
- Guardrail có hoạt động không.
- Trace có lưu không.

---

# 18. Test Plan

## Unit Test

Backend:

- Auth.
- Station service.
- Validation.
- Alert engine.
- Proposal service.

Agent:

- Intent.
- Tool selection.
- Tool schema.
- Guardrails.
- Proposal condition.

Frontend:

- Component render.
- API error.
- Route protection.

## Integration Test

- FE login → BE auth.
- FE dashboard → station API.
- Agent → backend API.
- MQTT → backend → DB.
- Alert engine → proposal API.
- Manager UI → approve/reject.

## E2E Test

### E2E-01

```text
S03 PM2.5 cao
→ MQTT
→ Backend
→ DB
→ Alert
→ Dashboard
→ Agent
→ Evidence
```

### E2E-02

```text
Outdoor user hỏi chạy bộ tại S05
→ Profile
→ Current PM2.5
→ Weather
→ Forecast
→ Recommendation
```

### E2E-03

```text
S03 sudden spike
→ Alert
→ Proposal pending
→ Manager approve/reject
→ Audit log
```

---

# 19. Definition of Ready

Task chỉ được bắt đầu khi:

- Có mô tả.
- Có owner.
- Có input/output.
- Có API hoặc tool contract.
- Có acceptance criteria.
- Có dependency.
- Không có blocking question.

---

# 20. Definition of Done

## API Done

- Endpoint chạy được.
- Request schema đúng.
- Response schema đúng.
- Error schema đúng.
- Swagger có mô tả.
- Có test.
- FE gọi được.
- Không đổi field ngoài contract.

## Tool Done

- Có tên.
- Có purpose.
- Có input.
- Có output.
- Có error.
- Có test.
- Có trace.
- Không vi phạm guardrail.

## Frontend Done

- Render đúng.
- Gọi API đúng contract.
- Có loading.
- Có error.
- Có empty state.
- Không trắng màn hình.
- Không hard-code production data.

---

# 21. Quy trình phối hợp

## FE cần API mới

1. FE mô tả màn hình.
2. FE ghi dữ liệu cần.
3. FE đề xuất request/response.
4. BE xác nhận.
5. Cập nhật README.
6. BE tạo mock endpoint.
7. FE tích hợp.
8. BE thay bằng logic thật.

## Agent cần Tool mới

1. Xác định intent.
2. Xác định purpose.
3. Định nghĩa input.
4. Định nghĩa output.
5. Định nghĩa error.
6. Map sang backend endpoint.
7. Tạo mock tool.
8. Viết test.
9. Nối API thật.
10. Cập nhật trace và metrics.

---

# 22. Environment Variables

## Backend

```env
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

DATABASE_URL=postgresql://airguard:change_me@localhost:5432/airguard

MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TOPIC=airguard/sensors/+/measurements

JWT_SECRET=change_me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

WEATHER_API_KEY=
LLM_API_KEY=
```

## Frontend

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Không để secret ở frontend.

---

# 23. Cách chạy local

Để hoàn thành và ký xác nhận toàn bộ Backend/Data-IoT trước demo, dùng
[Backend + Data/IoT Demo Completion Guide](docs/backend-data-iot-demo-completion.md). Guide này có
ma trận BE-001..BE-007/DI-001..DI-007, lệnh kiểm chứng, evidence pack và release blockers.

## Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 24. Thứ tự triển khai

## Phase 1 — Chốt contract

- API.
- Tool.
- Data.
- Error.
- Metrics.
- Test case.

## Phase 2 — Skeleton

- Backend routes trả mock.
- Frontend services gọi API.
- Agent tools đọc mock.
- Simulator tạo mock data.

## Phase 3 — Logic thật

- PostgreSQL.
- MQTT.
- Auth.
- Alert Engine.
- Agent orchestration.
- Proposal/HITL.

## Phase 4 — Integration

- FE–BE.
- Agent–BE.
- MQTT–BE–DB.
- Proposal–Manager UI.
- Audit log.

## Phase 5 — Evaluation

- 10 Agent tests.
- API tests.
- Data quality tests.
- 3 E2E scenarios.

---

# 25. Câu hỏi cần chốt

- Admin có bắt buộc không?
- Threshold PM2.5 dùng chuẩn nào?
- Bao nhiêu phút thì stale?
- Bao nhiêu phút thì offline?
- Forecast baseline có đủ không?
- Evidence có bắt buộc hiển thị trên UI không?
- Authentication thật hay demo account?
- Tool lỗi thì Agent trả lời một phần hay dừng?
- Agent được tự tạo proposal hay cần xác nhận trước?
