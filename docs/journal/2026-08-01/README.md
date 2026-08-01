# Nhat ky phat trien AirGuard AI - 2026-08-01

## Muc tieu trong ngay

Doc `AIRGUARD_AGENT_BRIEF.md` va tao MVP skeleton du de commit/push len GitHub, gom FastAPI, PostgreSQL schema, MQTT sensor simulator, React Leaflet dashboard, Docker Compose va tai lieu du an.

## Ket qua

Da hoan thanh skeleton AirGuard AI voi cac thanh phan:

- FastAPI backend va cac API stations, current measurement, history, alerts, health check.
- PostgreSQL schema ban dau cho stations, measurements, weather_observations, alerts, users, approval_requests, devices va audit_logs.
- Python MQTT simulator tao du lieu PM2.5 cho 5 vi tri demo.
- React Leaflet dashboard dung OpenStreetMap va 5 marker cam bien.
- Docker Compose cho backend, frontend, PostgreSQL, Mosquitto va simulator.
- Skeleton cho forecast service, AI Agent, approvals/HITL va device control, co TODO ro rang.
- README va bo tai lieu kien truc, API contract, backlog, user stories, agent tools va team roles.

## Backend da code

FastAPI app nam tai `backend/app/main.py`, phuc vu du lieu mock tu `data/stations.json`.

API chinh:

- `GET /health`
- `GET /api/v1/stations`
- `GET /api/v1/stations/{station_id}`
- `GET /api/v1/stations/{station_id}/current`
- `GET /api/v1/stations/{station_id}/history?hours=6`
- `GET /api/v1/alerts`
- `POST /api/v1/alerts/{alert_id}/resolve`
- `GET /api/v1/weather/current`
- `GET /api/v1/stations/{station_id}/forecast`
- `POST /api/v1/agent/chat`
- Cac endpoint placeholder cho approvals va devices.

`forecast_service.py` dang dung baseline forecast. `agent_service.py` chi tra loi placeholder; chua tich hop LLM, tool calling hay HITL that.

## Database da code

`backend/db/schema.sql` tao 8 bang:

1. `stations`
2. `measurements`
3. `weather_observations`
4. `alerts`
5. `users`
6. `devices`
7. `approval_requests`
8. `audit_logs`

Schema co index ban dau, seed 5 stations S01-S05 va thiet bi demo `FILTER-01`.

## MQTT simulator da code

`simulators/sensor_simulator/sensor_simulator.py`:

- Gia lap 5 diem PM2.5 quanh VinUniversity/Vinhomes Ocean Park.
- Tao bien dong theo PM2.5 nen, loai vi tri, gio cao diem, thoi tiet mock va nhieu ngau nhien.
- Publish measurement vao `airguard/stations/{station_id}/measurements`.
- Publish trang thai vao `airguard/stations/{station_id}/status`.
- Chu ky mac dinh co the cau hinh bang `SENSOR_INTERVAL_SECONDS`.

## Frontend da code

React dashboard nam trong `frontend/`:

- Vite + React 18.
- React Leaflet + Leaflet.
- OpenStreetMap tile layer.
- 5 CircleMarker PM2.5 co mau theo muc do.
- Lay danh sach tram tu backend, co mock fallback khi API khong kha dung.
- Responsive cho desktop va mobile.

Dependency frontend duoc ghim phien ban thay vi dung `latest` de build on dinh tren Node hien co.

## Cai dat da thuc hien

Moi lenh Python deu chay trong root `.venv`.

- `.venv` cu tro toi Python 3.13 trong WindowsApps va khong con truy cap duoc.
- Da nang cap venv tai cho sang Python 3.12.10 bang `python -m venv --upgrade .venv`.
- Da cai dependency backend va simulator vao `.venv`.
- Da cai dependency frontend va tao `frontend/package-lock.json`.

Python packages chinh:

- FastAPI 0.115.0
- Uvicorn 0.30.6
- Pydantic 2.8.2
- SQLAlchemy 2.0.32
- psycopg2-binary 2.9.9
- paho-mqtt 2.1.0
- python-dotenv 1.0.1

Frontend toolchain:

- Node.js 22.11.0
- npm 10.9.0
- React 18.3.1
- Leaflet 1.9.4
- React Leaflet 4.2.1
- Vite 6.4.3
- `@vitejs/plugin-react` 4.4.1

## Su co da xu ly

1. Venv khong khoi dong do tro toi Python 3.13 WindowsApps cu. Da nang cap tai cho sang Python 3.12.10.
2. Sandbox chan ket noi PyPI. Da cai dependency vao dung `.venv` sau khi cap quyen mang.
3. PowerShell chan `npm.ps1`. Da dung `npm.cmd`.
4. Node khong xac minh duoc TLS cua npm registry. Da tao CA bundle tam thoi tu Windows certificate store tai `C:\tmp\airguard-windows-roots.pem` va dung `NODE_EXTRA_CA_CERTS`.
5. `latest` keo Vite 8/Rolldown khong phu hop Node 22.11. Da ghim Vite 6.4.3 va plugin React 4.4.1.
6. `.gitignore` ban dau bo qua `data/stations.json`. Da sua de file 5 tram duoc commit.
7. Dockerfile frontend da doi sang `COPY package*.json ./` de ho tro repo co hoac chua co lockfile.

## Kiem thu da thuc hien

- Python `py_compile`: dat cho backend, services va simulator.
- Import FastAPI app trong `.venv`: dat.
- TestClient cho health, stations, current, history va alerts: deu HTTP 200.
- Parse `data/stations.json`: dat, du 5 stations.
- Kiem tra schema: co 8 lenh `CREATE TABLE`.
- Frontend production build: dat, 67 modules transformed.
- `npm audit`: 0 vulnerabilities.
- Backend dev server: `/health` tra HTTP 200.
- Frontend dev server: trang goc tra HTTP 200.
- `git diff --check`: dat, chi co canh bao LF/CRLF tren Windows.

## Gioi han hien tai

- May chua co lenh `docker`, nen chua chay duoc Docker Compose, PostgreSQL va Mosquitto thuc te.
- MQTT simulator moi duoc compile; chua test publish end-to-end vi Mosquitto chua chay.
- Browser backend cua phien coding khong kha dung, nen chua chup/kiem tra dashboard bang automation; production build va HTTP server da dat.
- Backend hien tra phan lon du lieu mock, chua doc/ghi PostgreSQL that.
- Chua co MQTT consumer, weather collector that, auth, AI Agent that, du bao production va HITL workflow hoan chinh.

Chi tiet cai dat va lenh chay xem [RUNBOOK.md](RUNBOOK.md). Danh sach file xem [FILES.md](FILES.md).
