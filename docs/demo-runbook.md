# Demo Runbook

## Before

Copy env, start Compose, confirm DB/broker/backend/Agent readiness, seed S01-S05, start
consumer/simulator/frontend, and verify `/stations` plus one MQTT-to-DB trace.

Verify the Agent path without using frontend fixture fallback:

```text
frontend :5173 -> backend POST :8000/api/v1/agent/chat
               -> Agent :8001/api/v1/agent/chat
               -> backend tool endpoints :8000/api/v1/*
```

## Scenarios

- A: normal map shows source/freshness.
- B: deterministic spike creates one alert.
- C: Agent answers current/forecast using tools and refuses missing data.
- D: a seeded demo profile asks for an outdoor recommendation; response separates current
  observation from forecast and carries the recommendation policy version.
- E: proposal pending -> manager reject/approve -> audit; device only if an acknowledged simulator
  exists.

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
