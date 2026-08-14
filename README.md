# AirGuard AI

AirGuard AI là MVP giám sát chất lượng môi trường tại Vinhomes Ocean Park 1 bằng 5 trạm mô phỏng. Hệ thống thu thập dữ liệu qua MQTT, lưu vào PostgreSQL, hiển thị dashboard AQI-first, tạo cảnh báo theo rule, dự báo ngắn hạn và cung cấp AI Agent có grounding cùng luồng Human-in-the-Loop (HITL).

> Toàn bộ dữ liệu môi trường hiện tại đến từ simulator phục vụ học tập và demo. Đây không phải hệ thống quan trắc được chứng nhận, không dùng để chẩn đoán sức khỏe, tuyên bố khẩn cấp hoặc ra quyết định y tế/pháp lý.

## Trạng thái hiện tại

| Khả năng | Trạng thái |
|---|---|
| 5 trạm S01–S05 | Đã có simulator, MQTT, PostgreSQL, API và UI |
| AQI realtime | AQI-first; tính sub-index từ PM2.5 theo breakpoint `US_EPA_PM25_24H_2012`, không phải AQI/NowCast chính thức |
| PM2.5, CO₂, tiếng ồn, nhiệt độ | Có trong simulator, validation, DB, API, lịch sử và UI |
| Dashboard realtime | Polling 30 giây khi tab hiển thị, có refresh và trạng thái fixture/error |
| Bản đồ khu vực | 5 trạm, vùng nhiệt trực quan, ranh giới Ocean Park 1, nền xám ngoài phạm vi |
| Dự báo 1–3 giờ | Damped linear trend từ tối thiểu 3 điểm fresh; hỗ trợ AQI, PM2.5, CO₂, tiếng ồn, nhiệt độ |
| Cảnh báo | Rule Engine deterministic cho 5 chỉ số và sensor offline |
| Khuyến nghị | Rule-owned recommendation trong alert; Agent recommendation theo profile và evidence cùng request |
| AI Agent | LangGraph/tool calling; grounded answer, có thể thêm giải thích bằng OpenAI nếu có key |
| HITL | Proposal bắt đầu `pending`; chỉ Manager approve/reject; có audit và device simulator |
| Notification | SMTP thật khi cấu hình `NOTIFICATION_PROVIDER=smtp`; mặc định `disabled` |
| Prophet/LSTM | Chưa triển khai |
| Mô hình lan truyền khoa học | Chưa có; vùng nhiệt chỉ trực quan hóa cường độ quanh trạm |

## Kiến trúc

```text
Sensor Simulator
  -> Mosquitto MQTT
  -> MQTT Consumer + validation/data-quality gate
  -> PostgreSQL
  -> FastAPI Backend (/api/v1)
  -> React/Vite Dashboard

Backend tool endpoints
  -> LangGraph Agent
  -> grounded response / recommendation / warning proposal
  -> Manager HITL
  -> audit + optional dispatcher/device simulator + optional SMTP
```

Ranh giới trách nhiệm:

- Backend là system of record; Frontend không đọc MQTT hoặc PostgreSQL trực tiếp.
- Rule Engine đặt ngưỡng/cảnh báo; LLM không tự đặt threshold.
- Agent chỉ dùng kết quả tool của cùng request, không đọc DB/MQTT trực tiếp.
- Dữ liệu invalid, stale hoặc station offline không dùng cho current, forecast, alert hoặc proposal.
- Agent không approve/reject proposal và không gửi device command trực tiếp.

## Công nghệ

- Frontend: React 18, TypeScript, Vite, React Leaflet, Recharts.
- Backend: FastAPI, Pydantic, PostgreSQL, Celery optional.
- Agent: LangGraph, LangChain OpenAI, typed tool contracts, trace/evaluation.
- Data/IoT: Mosquitto, Paho MQTT, simulator và consumer độc lập.
- Local: Docker Compose; RabbitMQ/Redis/Celery thuộc profile `async-jobs`.

## Chạy nhanh bằng Docker

### Yêu cầu

- Docker Desktop có Docker Compose.
- Tối thiểu 4 GB RAM trống cho stack cơ bản.
- OpenAI API key chỉ cần khi muốn dùng phần giải thích LLM thật.

### 1. Tạo cấu hình local

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash:

```bash
cp .env.example .env
```

Điền trong `.env` nếu dùng LLM:

```env
OPENAI_API_KEY=your_key_here
MODEL_NAME=gpt-4o-mini
```

Không commit `.env` hoặc đưa key vào log/screenshot.

### 2. Khởi động stack

```bash
docker compose up -d --build
docker compose ps
```

| Dịch vụ | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| Backend health | http://localhost:8000/health |
| Backend readiness | http://localhost:8000/ready |
| OpenAPI | http://localhost:8000/docs |
| Agent health | http://localhost:8001/health |
| PostgreSQL | `localhost:5432` |
| MQTT | `localhost:1883` |

Chờ ít nhất 2 chu kỳ simulator (mặc định 10 giây) trước khi đánh giá cảnh báo PM2.5 vì rule mặc định cần hai measurement liên tiếp.

### 3. Kiểm tra pipeline

```bash
docker compose logs --tail=50 sensor-simulator
docker compose logs --tail=50 mqtt-consumer
docker compose logs --tail=50 backend
```

PowerShell smoke test:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/stations
Invoke-RestMethod http://localhost:8000/api/v1/alerts?status=active
```

### 4. Bật async workers thật

Stack cơ bản dùng eager/in-memory cho demo. Để bật RabbitMQ, Redis và Celery:

```bash
docker compose --profile async-jobs up -d --build
```

### 5. Dừng

```bash
docker compose down
```

Không dùng `docker compose down -v` nếu muốn giữ database local.

## Xử lý lỗi Docker build

Nếu build dừng ở `RUN pip install --no-cache-dir -r requirements.txt`, chạy riêng backend để thấy lỗi đầy đủ:

```bash
docker compose build backend --no-cache --progress=plain
```

Kiểm tra:

- Docker Desktop còn chạy và có mạng/DNS.
- Proxy/VPN/firewall không chặn `pypi.org` hoặc `files.pythonhosted.org`.
- Ổ đĩa Docker còn dung lượng.
- Chạy `docker pull python:3.11-slim` để tách lỗi base image khỏi lỗi dependency.

Không dùng dòng `exit code: 2` cuối cùng để kết luận nguyên nhân; lỗi thật nằm ở các dòng pip phía trên.

## Dữ liệu môi trường

Topic measurement:

```text
airguard/stations/{station_id}/measurements
```

Ví dụ payload:

```json
{
  "message_id": "MSG-S01-0001",
  "station_id": "S01",
  "pm25": 42.5,
  "co2": 610,
  "noise_db": 58,
  "temperature": 30.1,
  "humidity": 72,
  "wind_speed": 2.4,
  "rainfall": 0,
  "timestamp": "2026-08-14T09:00:00+07:00",
  "source": "simulator"
}
```

`SENSOR_SCENARIO` hỗ trợ `normal`, `rush-hour`, `spike`, `recovery`, `duplicate`, `station-silence`.

Chỉ payload `valid`, fresh, đúng station/topic và có `source=simulator` mới đi vào downstream.

## AQI và các chỉ số

Dashboard dùng AQI làm chỉ số tổng quan. Chi tiết trạm hiển thị:

- AQI.
- PM2.5 (`µg/m³`).
- CO₂ (`ppm`).
- Tiếng ồn (`dB`).
- Nhiệt độ (`°C`).
- Source, timestamp, freshness và station status.

AQI hiện là PM2.5 concentration sub-index phục vụ demo. CO₂, tiếng ồn và nhiệt độ là chỉ số hỗ trợ, không phải thành phần trong công thức AQI hiện tại.

## Cảnh báo và khuyến nghị

Rule Engine tạo tối đa một active alert cho mỗi station/rule/version.

| Chỉ số | Warning mặc định | Critical mặc định |
|---|---:|---:|
| PM2.5 | 50 µg/m³ | 100 µg/m³ |
| AQI | 101 | 151 |
| CO₂ | 1000 ppm | 1500 ppm |
| Tiếng ồn | 70 dB | 85 dB |
| Nhiệt độ | 35 °C | 39 °C |

Đây là ngưỡng provisional cho MVP, không phải giới hạn y tế/pháp lý. Alert trả `metric`, `unit`, observed/threshold, severity và recommendation deterministic từ backend.

## Dự báo 1–3 giờ

Endpoint hỗ trợ `metric=pm25|aqi|co2|noise_db|temperature`:

- dùng 3–24 measurement hợp lệ trong 90 phút gần nhất;
- ước lượng linear trend, damp/cap biến động;
- trả forecast, khoảng bất định, confidence, model/source/freshness;
- trả `503 insufficient_forecast_history` nếu không đủ dữ liệu;
- không lặp current value để giả làm forecast.

```http
GET /api/v1/stations/S03/forecast?hours=3&metric=aqi
```

## AI Agent

Agent hỗ trợ current snapshot, impact assessment, history, compare, weather, forecast, alerts, profile, personalized recommendation, warning proposal và safety refusal.

Tool registry:

- `get_current_pm25` — tên legacy; output chứa AQI, PM2.5, CO₂, noise và temperature.
- `get_station_history`
- `compare_stations`
- `get_weather_context`
- `get_pm25_forecast`
- `get_active_alerts`
- `get_user_profile`
- `create_warning_proposal`

Luồng trả lời:

1. Router deterministic xác định intent và arguments allow-listed.
2. Agent gọi backend tools.
3. Quality gate loại dữ liệu missing/stale/offline/invalid.
4. Response composer tạo câu trả lời grounded.
5. Nếu có `OPENAI_API_KEY`, LLM chỉ thêm một câu giải thích giới hạn, không thay số liệu.
6. Trace ghi `generation_mode=live_llm` hoặc `deterministic_grounded`.

Prompt mẫu:

```text
Chất lượng môi trường tại S03 hiện tại thế nào?
Đánh giá mức độ ảnh hưởng môi trường tại S03.
So sánh S01 và S03.
Dự báo S03 trong 3 giờ tới.
Có cảnh báo nào tại S03?
Tôi có nên chạy bộ ngoài trời tại S03 không?
Tạo warning proposal cho S03.
```

## HITL, audit và notification

- Agent chỉ tạo proposal `pending` khi có fresh evidence và active alert.
- Chỉ role `manager` được approve/reject ở backend.
- Approve có thể tạo command intent; dispatcher mới publish MQTT.
- Reject không tạo device command.
- Proposal create/review/dispatch/failure có audit và correlation ID.
- SMTP gửi thật khi `NOTIFICATION_PROVIDER=smtp` và cấu hình SMTP hợp lệ.

Auth frontend hiện là demo identity, chưa phải authentication production.

## API chính

Base URL: `/api/v1`.

| Endpoint | Mục đích |
|---|---|
| `GET /health`, `GET /ready` | Health/readiness |
| `GET /stations` | Snapshot 5 trạm |
| `GET /stations/{id}/current` | AQI và các chỉ số |
| `GET /stations/{id}/history?hours=1..72` | Lịch sử |
| `POST /stations/compare` | So sánh trạm |
| `GET /stations/{id}/forecast` | Dự báo theo metric |
| `GET /alerts` | Alert đa chỉ số |
| `POST /agent/chat` | Agent qua backend proxy |
| `POST /proposals` | Tạo proposal pending |
| `GET /approvals` | Manager queue |
| `POST /approvals/{id}/approve` | Manager approve |
| `POST /approvals/{id}/reject` | Manager reject |
| `GET /audit-logs` | Audit cho manager |
| `GET /devices` | Device simulator state |

Chi tiết: [specs/api-contracts.md](specs/api-contracts.md).

## Biến môi trường quan trọng

| Biến | Ý nghĩa |
|---|---|
| `OPENAI_API_KEY` | Để trống: deterministic grounded response |
| `MODEL_NAME` | Mặc định `gpt-4o-mini` |
| `SENSOR_SCENARIO` | Mặc định `normal` |
| `STALE_AFTER_SECONDS` | Mặc định `300` |
| `PM25_ALERT_CONSECUTIVE_MEASUREMENTS` | Mặc định `2` |
| `*_WARNING_THRESHOLD`, `*_CRITICAL_THRESHOLD` | Threshold versioned/provisional |
| `NOTIFICATION_PROVIDER` | `disabled`; đặt `smtp` để gửi email |
| `SMTP_*` | Cấu hình SMTP secret/local |
| `CELERY_TASK_ALWAYS_EAGER` | `true` trong demo |

Xem đầy đủ tại [.env.example](.env.example).

## Chạy test

Python:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\ruff.exe check src tests
```

Frontend:

```powershell
Set-Location frontend
npm ci
npm run build
```

CI chạy Python test và frontend build. Ruff hiện chỉ báo annotation cho lint legacy và chưa chặn test trong workflow.

## Cấu trúc repository

```text
backend/                     FastAPI API, services, schema/seed
frontend/                    React/TypeScript dashboard
src/                         LangGraph Agent và Agent API
services/sensor-simulator/   MQTT environmental simulator
services/mqtt-consumer/      Validation + persistence
services/device-simulator/   Approved command simulator
infra/mqtt/                  Mosquitto configuration
data/                        Station catalog/fixtures
specs/                       API/data/domain contracts
adrs/                        Architecture decisions
tests/                       Backend, Agent, IoT, API tests
docs/                        Runbook, evaluation, PRD
tasks/                       Workstream/backlog plans
.ai-log/                     Handoff/session evidence
```

Runtime entry points:

- Backend: `backend/app/main.py`
- Frontend: `frontend/src/main.tsx` → `frontend/src/App.tsx`
- Agent: `src/main.py`
- Simulator: `services/sensor-simulator/sensor_simulator.py`
- Consumer: `services/mqtt-consumer/mqtt_consumer/main.py`
- Device simulator: `services/device-simulator/device_simulator.py`

## Tài liệu liên quan

- [AGENTS.md](AGENTS.md): handoff và nguyên tắc coding agent.
- [PRD](docs/Gate%201/PRD.md): yêu cầu sản phẩm hiện hành.
- [API contracts](specs/api-contracts.md).
- [Data contracts](specs/data-contracts.md).
- [Domain model](specs/domain-model.md).
- [Agent evaluation](docs/agent-evaluation.md).
- [Demo runbook](docs/demo-runbook.md).
- [ADR forecast](adrs/0007-short-term-trend-forecast.md).
- [ADR multi-metric alerts](adrs/0009-multi-metric-environmental-alerts.md).

## Known limitations

- Sensor và phần lớn weather context là simulator/fallback.
- AQI là PM2.5 sub-index đơn giản, chưa phải official AQI/NowCast.
- Forecast là baseline trend, chưa có Prophet/LSTM/backtesting production.
- Heat zones không phải mô hình lan truyền ô nhiễm khoa học.
- Threshold CO₂/noise/temperature cần mentor/operations xác nhận.
- Authentication/RBAC frontend còn ở mức demo.
- SMTP và async worker production cần cấu hình hạ tầng/secret riêng.
