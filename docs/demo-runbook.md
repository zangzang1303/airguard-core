# Demo Runbook

## Before

Copy env, start Compose, confirm DB/broker/API readiness, seed S01-S05, start consumer/simulator/frontend, verify `/stations` and one MQTT->DB trace.

## Scenarios

A: normal map shows source/freshness. B: deterministic spike creates one alert. C: Agent answers current/forecast using tools and refuses missing data. D: proposal pending -> manager reject/approve -> audit; device only if acknowledged simulator exists.

## Roles

Presenter; operator; log observer; fallback owner. Capture message/request/proposal ids.

### Demo access (frontend-only)

Auth provider production chua duoc chot. Man hinh Login hien ba identity seed chi de demo UI/RBAC:

| Role | Email | Mat khau demo | Pham vi UI |
|---|---|---|---|
| Resident | `resident@vinuni.edu.vn` | `AirGuard@2026` | Dashboard, AI Agent, Canh bao, Ho so |
| Manager | `manager@vinuni.edu.vn` | `AirGuard@2026` | Resident + Phe duyet + Audit Log |
| Admin | `admin@vinuni.edu.vn` | `AirGuard@2026` | Toan bo surface MVP |

Day khong phai credential production. Registration tao Resident trong memory cua phien browser hien tai; refresh trang se xoa tai khoan vua tao. Manager/Admin chi duoc cap san, khong the self-register hoac doi role tu Profile. Backend RBAC van la system of record khi auth contract duoc tich hop.

## Failure handling

Do not invent live data. State outage, show labeled fixture only if prepared, or skip affected scenario. After demo, archive evidence and known limitations.
