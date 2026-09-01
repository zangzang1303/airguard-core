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

`db-migrate` applies the additive authentication, Auto Ventilation/Report, demo device mapping and UTF-8 Vietnamese
station/alert repair migrations before the backend starts. Existing named volumes are preserved. To
enable scheduled daily/weekly reports, start the async profile, which includes RabbitMQ, Redis,
Celery worker and Celery Beat:

```powershell
$env:CELERY_TASK_ALWAYS_EAGER="false"
docker compose --profile async-jobs up -d --build
Remove-Item Env:CELERY_TASK_ALWAYS_EAGER
```

The explicit override is required because the core profile defaults to eager execution so it can
run without RabbitMQ. Verify `celery-worker`, `celery-beat`, `rabbitmq` and `redis` are running.

The public demo topology runs the same one-shot migration gate before starting the backend:

```powershell
docker compose --env-file /path/to/airguard-demo.env -f docker-compose.public-demo.yml up -d --build
```

Beat uses `REPORT_TIMEZONE` (default `Asia/Ho_Chi_Minh`): daily at 00:10 and weekly at 00:20 on
Monday. Scheduled/manual retries reuse the same persisted report range rather than creating a
second record.

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

### Apply the Auto Ventilation and Report migration

Compose applies this migration through `db-migrate`. For an existing database managed outside
Compose, apply it explicitly after the authentication migration:

```powershell
Get-Content -Raw backend/db/migrations/20260821_002_auto_ventilation_reports.sql |
  docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U airguard -d airguard
```

The migration is additive and safe to re-run. It adds proposal control/review metadata, durable
device-command ACK events and persisted environmental reports; it does not approve or dispatch any
proposal.

### Repair Vietnamese station and alert text

Compose applies this migration through `db-migrate`. For an existing database, apply it explicitly
once (it is safe to re-run) to replace legacy mojibake or `?` characters in station metadata and
alert copy:

```powershell
Get-Content -Raw backend/db/migrations/20260823_003_fix_vietnamese_station_names_and_alerts.sql |
  docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U airguard -d airguard
```

Verify the repair through the backend API after restarting the stack:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/stations
Invoke-RestMethod "http://localhost:8000/api/v1/alerts?status=active"
```

### Repair Vietnamese demo user display names

Compose applies this migration through `db-migrate`. For an existing database volume, apply it explicitly once (it is idempotent, safe to re-run and does not create new users) to restore corrupted UTF-8 names for the three demo accounts:

```powershell
Get-Content -Raw backend/db/migrations/20260823_004_fix_vietnamese_demo_user_names.sql |
  docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U airguard -d airguard
```

Verify that the demo user names are properly restored:

```powershell
docker compose exec -T postgres psql -U airguard -d airguard -c "SELECT email, full_name FROM users WHERE LOWER(BTRIM(email)) IN ('manager@vinuni.edu.vn', 'admin@vinuni.edu.vn', 'resident@vinuni.edu.vn') ORDER BY email;"
```

## Resend Email API Configuration

To enable real email dispatch for account verification and manager notifications:

1. **Create Resend account**: Register at [resend.com](https://resend.com).
2. **Add sending domain**: Add your sending subdomain (e.g. `mail.example.com`).
3. **Configure DNS**: Add SPF and DKIM TXT/MX records according to Resend Dashboard instructions.
4. **Wait for domain verification**: Confirm domain status shows `Verified`.
5. **Create API key**: Create a restricted API Key with `Sending access` scoped to the verified domain.
6. **Set environment variables** in `.env`:
   ```env
   NOTIFICATION_PROVIDER=resend
   RESEND_API_KEY=re_your_api_key_here
   RESEND_FROM_EMAIL=AirGuard AI <no-reply@mail.example.com>
   RESEND_FROM_NAME=AirGuard AI
   RESEND_TIMEOUT_SECONDS=10
   FRONTEND_URL=https://your-frontend-domain.com
   ```
7. **Production reminder**: Never hardcode `onboarding@resend.dev` in production (it is restricted to account owner email). Ensure `FRONTEND_URL` uses production HTTPS so verification/reset links point to the right origin.

