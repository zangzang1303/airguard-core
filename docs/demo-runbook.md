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

## Automatic proposal demo

Set `AUTO_PROPOSAL_ENABLED=true` and configure a real `OPENAI_API_KEY`. A new eligible
environmental alert invokes the Agent without any resident chat request. After a successful
live-LLM analysis, the Agent creates one `pending` proposal for Manager review. If the provider
fails, the alert stays active and the audited result is a skip, not a deterministic proposal.

## Personalized alert and clean-running route demo (B7-02)

1. Start the base stack and confirm at least three stations are `online`, `fresh`, `valid`, and
   sourced from `simulator`. Do not continue this scenario with fixture fallback.
2. Call `POST /api/v1/exposure/inhaled-mass` for S01, `running`, 30 minutes. Confirm the response
   uses `estimated_inhaled_mass_ug`, includes source/time/policy/disclaimer, and does not describe
   absorbed dose or a medical conclusion.
3. Select an origin on the map and ask the Agent for a 5 km running route. Compare the Agent
   `highlight_route` with `POST /api/v1/routes/clean-running`: route ID, geometry, segment doses,
   totals and graph provenance must be identical. Source must remain `curated_demo_graph`.
4. As a resident, enable only `predictive_email_enabled`; leave the environmental opt-in unchanged
   to demonstrate independent consent. Preference writes require the session CSRF token.
5. As Manager, call predictive evaluate with `dry_run=true` first and verify no notification job is
   created. Enable the feature flag only for the controlled async demo, then evaluate a qualifying
   station with `dry_run=false` during the 30–60 minute lead window.
6. The worker must revalidate the current snapshot, forecast quality, active-alert state and
   recipient consent immediately before the Resend/mock call. Repeating the same episode/severity/user
   must reuse the idempotency key instead of sending again.
7. Open the generated URL. It must contain only `panel`, `station_id`, and
   `predictive_warning_id`; the app flies to the backend station, opens detail, and checklist PUT
   requires authentication plus CSRF. The checklist never creates a device command.

Run the async path with `docker compose --profile async-jobs up -d --build`. If the Docker daemon,
PostgreSQL, Redis/RabbitMQ, or Resend mock is unavailable, record the exact blocker and do not mark
the Compose integration as passed. Provider `accepted` is not inbox-delivery proof.

## ESG periodic report demo (B7-05)

1. Run the migration chain twice and confirm `20260829_007_esg_reports.sql` reports only safe
   existing-object notices on the second pass. Query `device_operating_profiles` and show that the
   `FILTER-01` seed is versioned, simulated and explicitly not field calibration.
2. Start `docker compose --profile async-jobs up -d --build`. Daily Beat remains 00:10 and weekly
   Beat remains Monday 00:20 in `REPORT_TIMEZONE`. Manual and Beat requests for the same half-open
   identity must return the same report ID.
3. Sign in as Manager, open Reports, generate a weekly report and select `all_stations`, then one
   station. Confirm every persisted view contains 168 cells; N/A cells are hatched and do not use a
   good-air color. Tooltip shows sample/expected counts, coverage and station counts.
4. Keep QCVN, WHO and internal 85 percent KPI in separate UI blocks. QCVN must say
   `not_comparable`; WHO must be labeled guideline; no annual compliance conclusion is allowed.
5. If there are no qualifying ACK/profile/windows, confirm both ESG values are null with
   `insufficient_data` and a reason code while the report itself remains completed. Never substitute
   zero or an environmental default.
6. Exercise an unavailable or malformed narrative provider. The entire live narrative must fall
   back to `deterministic_grounded`; statistics, checksum and export remain available.
7. Download Markdown, HTML and PDF. Confirm all contain the same report ID and SHA-256 as the API.
   Exports must not trigger measurement/device source queries. Render the PDF with Poppler before the
   demo and inspect A4 pages, Vietnamese glyphs, repeated table headers, watermark, disclaimer and
   the vector 7x24 matrix.

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
