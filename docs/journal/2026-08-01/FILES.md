# Danh muc file AirGuard AI

## File root da sua

- `.env.example`: bien moi truong cho app, database, MQTT, map va placeholder API keys.
- `.gitignore`: giu `data/stations.json` trong Git, bo qua venv, node_modules, dist va du lieu runtime.
- `README.md`: tong quan, scope, kien truc, setup, demo flow va tai lieu lien quan.
- `docker-compose.yml`: PostgreSQL, Mosquitto, FastAPI, React frontend va sensor simulator.

## Backend da tao

- `backend/Dockerfile`
- `backend/requirements.txt`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/services/__init__.py`
- `backend/app/services/agent_service.py`
- `backend/app/services/forecast_service.py`
- `backend/db/schema.sql`

## Data da tao

- `data/stations.json`: 5 tram S01-S05 va toa do demo.

## MQTT va simulator da tao

- `mqtt/mosquitto.conf`
- `simulators/sensor_simulator/Dockerfile`
- `simulators/sensor_simulator/requirements.txt`
- `simulators/sensor_simulator/sensor_simulator.py`

## Frontend da tao

- `frontend/Dockerfile`
- `frontend/README.md`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/main.jsx`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`

## Tai lieu da tao

- `docs/api-contract.md`
- `docs/architecture.md`
- `docs/backlog.md`
- `docs/user-stories.md`
- `docs/team-roles.md`
- `docs/agent-tools.md`
- `docs/journal/2026-08-01/README.md`
- `docs/journal/2026-08-01/RUNBOOK.md`
- `docs/journal/2026-08-01/FILES.md`

## File dau vao

- `AIRGUARD_AGENT_BRIEF.md`: brief goc dung lam yeu cau trien khai; file nay da co trong workspace va khong phai noi dung do coding agent tu tao.

## File sinh ra khong can commit

- `.venv/`: moi truong ao Python local.
- `frontend/node_modules/`: npm dependencies local.
- `frontend/dist/`: output production build.
- `C:\tmp\airguard-windows-roots.pem`: CA bundle tam thoi phuc vu npm tren may hien tai.


## Celery background job files da tao

- backend/app/celery_app.py
- backend/app/tasks/__init__.py
- backend/app/tasks/task_support.py
- backend/app/tasks/agent_tasks.py
- backend/app/tasks/forecast_tasks.py
- backend/app/tasks/notification_tasks.py
- backend/app/services/job_service.py
- backend/app/services/approval_service.py
