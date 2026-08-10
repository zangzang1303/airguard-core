# Backend + Data/IoT Verification Evidence

> Copy file này vào `docs/evidence/backend-data-iot/<date>-run-<number>/` cho mỗi rehearsal.
> Không ghi secret, `.env`, token, password, raw sensitive prompt hoặc PII.

## Run metadata

| Field | Value |
|---|---|
| Date/time + timezone | TBD |
| Git commit | TBD |
| Operator | TBD |
| Reviewer | TBD |
| Docker/Compose version | TBD |
| Scenario seed | TBD |
| Rule version | TBD |
| Stale/offline policy | TBD |
| Weather mode/source | TBD |
| Device simulator enabled | Yes/No |

## Commands and results

| Command | Expected | Actual | Exit/result | Evidence file |
|---|---|---|---|---|
| `python -m pytest -q` | All required tests pass | TBD | Pending | TBD |
| `npm.cmd --prefix frontend run build` | Exit 0 | TBD | Pending | TBD |
| `docker compose config --quiet` | Exit 0 | TBD | Pending | TBD |
| `docker compose up -d --build ...` | Required services healthy | TBD | Pending | TBD |

## Normal message trace

| Field | Simulator | Consumer | PostgreSQL | API | UI |
|---|---|---|---|---|---|
| message_id | TBD | TBD | TBD | TBD | N/A/history |
| station_id | TBD | TBD | TBD | TBD | TBD |
| pm25 | TBD | TBD | TBD | TBD | TBD |
| timestamp | TBD | TBD | TBD | TBD | TBD |
| source | simulator | simulator | simulator | simulator | simulator label |
| request/correlation ID | N/A | TBD | N/A | TBD | TBD |

## Data-quality matrix

| Case | Expected | Actual | Rejection reason | Current unchanged | Alert/proposal blocked | Result |
|---|---|---|---|---|---|---|
| Malformed JSON | Reject | TBD | `malformed` | TBD | TBD | Pending |
| Unknown station | Reject | TBD | `unknown_station` | TBD | TBD | Pending |
| Topic mismatch | Reject | TBD | `topic_station_mismatch` | TBD | TBD | Pending |
| Negative/range | Reject | TBD | `range_error` | TBD | TBD | Pending |
| Future | Reject | TBD | `future_time` | TBD | TBD | Pending |
| Stale | Reject | TBD | `stale` | TBD | TBD | Pending |
| Duplicate | Ignore idempotently | TBD | `duplicate` | TBD | TBD | Pending |
| Out-of-order | Persist/history per policy; not current | TBD | N/A | TBD | TBD | Pending |

## Alert matrix

| Case | Message IDs | Expected | Alert ID/rule version | Actual | Result |
|---|---|---|---|---|---|
| Below/equal threshold | TBD | No active PM2.5 alert | TBD | TBD | Pending |
| Consecutive spike | TBD | One active alert | TBD | TBD | Pending |
| Repeated spike | TBD | No duplicate alert | TBD | TBD | Pending |
| Invalid/stale spike | TBD | No alert | TBD | TBD | Pending |
| Recovery | TBD | Alert resolved | TBD | TBD | Pending |
| Station silence/offline | TBD | Policy-defined offline alert/status | TBD | TBD | Pending |

## HITL and audit trace

| Step | Proposal ID | Version | Actor/role | Expected | Audit ID/outcome | Result |
|---|---|---|---|---|---|---|
| Create | TBD | 1 | Agent | pending | TBD | Pending |
| Viewer review | TBD | 1 | viewer | 403 | failure/denied if audited | Pending |
| Reject | TBD | 1 | manager | rejected, no dispatch | TBD | Pending |
| Approve | TBD | 1 | manager | approved | TBD | Pending |
| Double review | TBD | stale version | manager | 409 | TBD | Pending |
| Dispatch | TBD | terminal | backend | only after approve | TBD | Pending |
| Device ack | TBD | terminal | simulator | `is_simulated=true` | TBD | Pending/Deferred |

## Failure drills

| Failure | Expected | Actual | Recovery command/time | Result |
|---|---|---|---|---|
| PostgreSQL down | ready 503, no silent loss | TBD | TBD | Pending |
| MQTT down | reconnect, no invented data | TBD | TBD | Pending |
| Consumer restart | resume, no duplicate current | TBD | TBD | Pending |
| Agent down | structured 503 | TBD | TBD | Pending |
| Weather unavailable | labeled fallback/unavailable | TBD | TBD | Pending |
| Worker down | actionable failed state | TBD | TBD | Pending |
| Device timeout | failed/pending, never succeeded | TBD | TBD | Pending |

## Known limitations

- TBD

## Sign-off

| Gate | Owner | Result | Evidence | Signed at |
|---|---|---|---|---|
| Backend unit/contract | TBD | Pending | TBD | TBD |
| MQTT/Data Quality | TBD | Pending | TBD | TBD |
| Alert | TBD | Pending | TBD | TBD |
| HITL/Audit | TBD | Pending | TBD | TBD |
| Weather provenance | TBD | Pending | TBD | TBD |
| Device ack | TBD | Pending/Deferred | TBD | TBD |
| Full rehearsal | TBD | Pending | TBD | TBD |

Final decision: `PENDING | DEMO-READY | BLOCKED`

