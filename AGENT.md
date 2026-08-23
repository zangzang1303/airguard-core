# AirGuard AI — Agent Quick Handoff

> Read this file first. For binding engineering rules and full contracts, read `AGENTS.md` next.

## 1. Product and scope

AirGuard AI is an MVP dashboard for **simulated** air-quality monitoring around Vinhomes Ocean Park 1. It uses five stations (S01–S05) and shows AQI, PM2.5, CO2, noise and temperature. The product is a learning/demo system, **not official monitoring, medical advice, or real device control**.

Core flow:

```text
Sensor simulator → MQTT → consumer/validation → PostgreSQL → FastAPI → React dashboard
                                                     ↘ AI Agent / approvals / audit / device simulator
```

## 2. Current live state

- Working branch: `Canh`
- Live demo: `https://airguard-074-demo-2302.indonesiacentral.cloudapp.azure.com`
- Pushes to `Canh` trigger Azure deployment: `.github/workflows/deploy-azure.yml`.
- Team remote is `origin`; its push configuration also mirrors to `zangzang1303/airguard-core`.
- Before claiming a change is live, check the GitHub Actions deployment and smoke-test the live URL.

## 3. Implemented capabilities to preserve

1. MQTT simulator pipeline, quality/freshness status and 5-station dashboard.
2. Wind-adjusted IDW heatmap; current and forecast horizon visualization.
3. Prophet-inspired 1–24 hour time-series forecast. Present it as an MVP forecast, not certified forecasting.
4. Grounded AI Agent: answer only from backend tool evidence; gracefully state insufficient data/tool failure.
5. Personalized running-area/route suggestions based on air quality, health profile, desired distance and map location.
6. Three health profiles: normal, sensitive, outdoor sport.
7. Auto-ventilation proposal flow: pollution rule → pending proposal → Manager quick approval → device simulator ACK → audit. Never bypass Manager HITL.
8. Daily/weekly environmental reports with Markdown, HTML and PDF export.
9. Manager/Admin demo station control: floating map panel with station selector, metric sliders, Apply, and return-to-auto simulation. It is demo-only and must remain clearly labeled.

## 4. Important UI expectation

The demo station control is intentionally a **floating map panel**, not part of the AI chat drawer. Main files:

- `frontend/src/features/drawers/DemoStationControl.tsx`
- `frontend/src/App.tsx`
- `frontend/src/features/drawers/AiAssistantDrawer.tsx`

Do not re-add `DemoStationControl` to `AiAssistantDrawer.tsx` unless the product owner explicitly changes this decision.

## 5. Main code map

| Concern | Start here |
|---|---|
| REST API / business logic | `backend/app/main.py`, `backend/app/services/` |
| Dashboard | `frontend/src/App.tsx`, `frontend/src/features/` |
| AI Agent | `src/agents/`, `src/api/` |
| Sensor pipeline | `services/sensor-simulator/`, `services/mqtt-consumer/` |
| Device simulator | `services/device-simulator/` |
| Data contracts | `specs/api-contracts.md`, `specs/data-contracts.md`, `specs/domain-model.md` |
| Tests | `tests/test_backend/`, `tests/test_agents/` |
| Deployment | `.github/workflows/deploy-azure.yml`, `docs/azure-auto-deploy.md` |

## 6. Non-negotiable rules

- Do not invent environmental facts, forecasts, alerts, device state or user data. Backend evidence is the source of truth.
- Do not let the frontend access MQTT or PostgreSQL directly.
- Do not auto-approve, send direct Agent-to-MQTT commands, or alter audit history.
- Exclude invalid/stale/offline data from current values, warnings and forecasts.
- Keep `source=simulator` visible where appropriate.
- Never commit `.env`, keys, tokens, passwords or OAuth credentials.
- When contracts change, update specs and tests in the same change.

## 7. Safe working procedure

1. Read `AGENTS.md`, the relevant `tasks/*.md`, specs and ADR before implementation.
2. Run `git status -sb`; preserve all existing changes.
3. Use `rg` to trace the feature before editing.
4. Implement the smallest scoped change, then run focused tests/build.
5. Update docs/tests/contracts when behavior changes.
6. Commit only intended files; do not use `git add .` blindly.

### Branch sync

If `git push origin Canh` is rejected, first preserve local work, then rebase:

```powershell
git stash push -u -m "WIP before syncing Canh"
git pull --rebase origin Canh
git stash pop
git push origin Canh
```

Resolve conflicts deliberately. Never force-push `Canh`. A local `.route-ui/` directory may be a separate worktree; never stage it from the root repository.

## 8. Local run and verification

```powershell
docker compose up --build -d
```

Check dashboard, backend health, Agent health, all five station values, freshness, heatmap, forecast, alerts, Agent grounding and Manager approval flow. See `docs/environment-setup.md` and `docs/demo-runbook.md` for details.

## 9. Known limits to state honestly

- Simulator data, not official observation.
- AQI is derived from PM2.5 for this MVP.
- Heatmap is wind-adjusted IDW visualization, not a physical dispersion model.
- Forecast is a lightweight Prophet-inspired baseline; accuracy claims require evaluation evidence.
- Device actions target a simulator and remain Manager-approved.

## 10. Handoff checklist

Before ending a material task: record modified files, decisions, tests run, unresolved risks and the exact next step in `.ai-log/` using `templates/ai-log-template.md`.
