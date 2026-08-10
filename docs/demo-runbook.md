# Demo Runbook

Backend/Data-IoT lead phải hoàn tất và ký các gate trong
[Backend + Data/IoT Demo Completion Guide](backend-data-iot-demo-completion.md) trước full-system
rehearsal. Runbook này không thay cho task-level evidence pack.

## Before

Copy env, start Compose, confirm DB/broker/backend/Agent readiness, seed S01-S05, start
consumer/simulator/frontend, and verify `/stations` plus one MQTT-to-DB trace. For an
existing local DB volume, run `.\scripts\init-demo-db.ps1` before starting the simulator.

Verify the Agent path without using frontend fixture fallback:

```text
frontend :5173 -> backend POST :8000/api/v1/agent/chat
               -> Agent :8001/api/v1/agent/chat
               -> backend tool endpoints :8000/api/v1/*
```

## Scenarios

- A: normal map shows source/freshness.
- B: deterministic spike creates one alert.
- B1: repeated valid spike meets the configured consecutive-measurement gate; duplicate/stale
  samples do not create another alert.
- C: Agent answers current/forecast using tools and refuses missing data.
- D: a seeded demo profile asks for an outdoor recommendation; response separates current
  observation from forecast and carries the recommendation policy version.
- E: proposal pending -> manager reject/approve -> audit; device only if an acknowledged simulator
  exists.

The local seed provides the resident, manager and admin demo profiles used by the dashboard. These
are demo identities only; they are not production credentials or authentication.

For Scenario D, the backend user profile must exist and the profile/alert/weather tool responses
must match the Agent tool contracts. Do not replace a missing profile or tool error with a
client-supplied user group.

## Roles

Presenter; operator; log observer; fallback owner. Capture message/request/proposal ids.

### Demo access (frontend-only)

Auth provider production chua duoc chot. Man hinh Login hien ba identity seed chi de demo UI/RBAC:

| Role | Email | Mat khau demo | Pham vi UI |
|---|---|---|---|
| Resident | `resident@vinuni.edu.vn` | `AirGuard@2026` | Dashboard, AI Agent, Canh bao, Ho so |
| Manager | `manager@vinuni.edu.vn` | `AirGuard@2026` | Resident + Phe duyet + Audit Log |
| Admin | `admin@vinuni.edu.vn` | `AirGuard@2026` | Toan bo surface MVP |

Day khong phai credential production. Registration tao Resident trong memory cua phien browser
hien tai; refresh trang se xoa tai khoan vua tao. Manager/Admin chi duoc cap san, khong the
self-register hoac doi role tu Profile. Backend RBAC van la system of record khi auth contract duoc
tich hop.

## Failure handling

Do not invent live data. State outage, show a labeled fixture only if explicitly prepared outside
Agent chat, or skip the affected scenario. After demo, archive evidence and known limitations.

The default demo rule requires two consecutive fresh measurements above the warning threshold
(`PM25_ALERT_CONSECUTIVE_MEASUREMENTS=2`). Wait for two simulator intervals before judging the
spike result.
If PostgreSQL was created before the current schema, run the safe local bootstrap
before starting the demo:

```powershell
.\scripts\init-demo-db.ps1
```
