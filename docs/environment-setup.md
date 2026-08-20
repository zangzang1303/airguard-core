# Environment Setup

Quy trình kiểm chứng Backend/Data-IoT và release sign-off nằm tại
[Backend + Data/IoT Demo Completion Guide](backend-data-iot-demo-completion.md).

Install Docker Desktop/Compose, Python and Node versions required by project files. Copy
`.env.example` to `.env`; supply only local secrets and never commit it.

## Compose topology

Start the full local stack:

```powershell
docker compose up --build
```

The development frontend bind-mounts `frontend/src` and the Vite/TypeScript
configuration, while `node_modules` stays inside the rebuilt image. Source and
style edits therefore keep Vite HMR, and dependency changes require rebuilding
the frontend service:

```powershell
docker compose up -d --build --force-recreate frontend
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
consumer/worker, sensor simulator, device simulator and frontend. Verify `/health` for backend/Agent, backend readiness,
`GET /api/v1/stations`, MQTT publish logs and dashboard.

The default Compose profile uses `PM25_ALERT_CONSECUTIVE_MEASUREMENTS=2` and generates a unique
simulator run prefix for `message_id`. Set `SENSOR_RUN_ID` only when a deterministic run identifier
is required for evidence; do not reuse it against a persistent demo database.

Troubleshoot:

- Backend `agent_unavailable`/`agent_timeout`: inspect Agent service and `AGENT_SERVICE_URL`.
- Agent tool failures: inspect backend readiness and `AGENT_BACKEND_BASE_URL`.
- Empty map: verify seed/API/CORS.
- No fresh data: inspect simulator topic, consumer log and `last_seen`.
- Never bypass validation with DB edits; record local deviations in an AI log.
## Initialize an existing local database

PostgreSQL runs `schema.sql` and `seed.sql` automatically only when its named volume
is first created. If an existing local volume predates the current schema, apply the
idempotent demo bootstrap without deleting data:

```powershell
.\scripts\init-demo-db.ps1
```

This is for local demo environments only. Do not use it as a replacement for a
versioned migration process in a shared or production database.

### Apply the authentication foundation migration

The bootstrap schema contains the authentication storage for a newly created database.
For an existing database, apply the additive migration without deleting the volume:

```powershell
Get-Content -Raw backend/db/migrations/20260820_001_auth_foundation.sql |
  docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U airguard -d airguard
```

The migration is transactional and safe to re-run. It intentionally fails when legacy
users contain emails that differ only by letter case; resolve those identities manually
before retrying. The migration stores only token hashes and does not enable login APIs or
replace the current demo-header RBAC by itself.
