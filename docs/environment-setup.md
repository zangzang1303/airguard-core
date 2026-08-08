# Environment Setup

Install Docker Desktop/Compose, Python and Node versions required by project files. Copy
`.env.example` to `.env`; supply only local secrets and never commit it.

## Compose topology

Start the full local stack:

```powershell
docker compose up --build
```

The relevant HTTP services are:

| Service | Local URL | Responsibility |
|---|---|---|
| Backend | `http://localhost:8000` | System of record, tools and canonical frontend API |
| Agent | `http://localhost:8001` | Grounded graph; HTTP access to backend only |
| Frontend | `http://localhost:5173` | Dashboard and Agent chat UI |

The backend proxies `POST /api/v1/agent/chat` to the Agent service. In Compose,
`AGENT_SERVICE_URL=http://agent:8001` and `AGENT_BACKEND_BASE_URL=http://backend:8000`. Do not put
`DATABASE_URL`, MQTT credentials or broker access in the Agent service environment.

## Manual local processes

Run backend on port 8000, then start the root Agent on port 8001:

```powershell
$env:APP_PORT="8001"
$env:AGENT_BACKEND_BASE_URL="http://localhost:8000"
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

Start dependencies first (PostgreSQL, Mosquitto), then migrations/seed, backend, Agent,
consumer/worker, simulator and frontend. Verify `/health` for backend/Agent, backend readiness,
`GET /api/v1/stations`, MQTT publish logs and dashboard.

Troubleshoot:

- Backend `agent_unavailable`/`agent_timeout`: inspect Agent service and `AGENT_SERVICE_URL`.
- Agent tool failures: inspect backend readiness and `AGENT_BACKEND_BASE_URL`.
- Empty map: verify seed/API/CORS.
- No fresh data: inspect simulator topic, consumer log and `last_seen`.
- Never bypass validation with DB edits; record local deviations in an AI log.
