# AI Work Log

## Date / agent / machine

- 2026-08-23 / Codex / Windows workspace

## Goal

- Deploy the latest AirGuard AI revision to the public Render and Vercel surfaces.

## Context read

- `AGENTS.md`
- `render.yaml`
- `frontend/.vercel/project.json`
- `frontend/vercel.json`
- `backend/app/core.py`
- `backend/app/services/station_service.py`
- `backend/app/services/spatial_dispersion_service.py`

## Files changed

- `.env.example`: documents the public Vercel origin in `CORS_ORIGINS`.
- `backend/app/core.py`: allows the public Vercel origin when `CORS_ORIGINS` is absent.
- `tests/test_backend/test_services.py`: guards the production-origin default.

## Decisions and rationale

- Kept the heatmap data-quality gate intact. It must not use the in-process simulator fallback when persisted station snapshots are unavailable.
- Added only the known public frontend origin to the backend default; no wildcard CORS origin was introduced.
- Pushed the same revision to `origin/main`, `origin/Canh`, and `myrepo/main` because the public services' exact Git integration branch was not visible from the workspace.

## Commands/tests run and results

- Frontend production build passed before deployment.
- All six Compose application images built successfully before deployment.
- `python -m compileall -q backend/app/core.py tests/test_backend/test_services.py`: passed.
- Direct `Settings.load()` assertion for `https://airguard-app.vercel.app`: passed.
- `git diff --check`: passed.
- Full pytest rerun was unavailable because Docker Desktop stopped responding after an I/O error.
- Render CORS preflight changed from HTTP 400 to HTTP 200 after commit `b22ed46` deployed.
- Public backend health is HTTP 200 and returns five fresh online simulator stations.

## Contracts/risks changed

- Production CORS default now includes only `https://airguard-app.vercel.app` plus the two existing local development origins.
- Render still has no `DATABASE_URL`; readiness, persisted alerts, reports, HITL/audit, and grounded heatmap paths cannot be considered production-ready.
- Vercel still serves the old `index-G3UVgYq4.js` asset; Git pushes did not trigger a visible production promotion.

## Blockers/open questions

- The current machine has no Vercel or Render API credential, and the connected browser control surface failed to initialize.
- A real PostgreSQL connection string must be configured in Render; it must not be guessed or committed.
- Vercel requires an authenticated redeploy or corrected Git integration/root-directory setting.

## Next exact step

1. In Render `airguard-core`, set `DATABASE_URL`, `CORS_ORIGINS`, and `FRONTEND_URL`, then redeploy.
2. In Vercel `airguard-app`, set Root Directory to `frontend`, select the active production branch, and redeploy commit `b22ed46`.
3. Run `/ready`, stations, alerts, heatmap, auth, reports, Agent, HITL, and browser smoke tests.

## Handoff IDs (request/message/proposal/job)

- Git deployment revision: `b22ed46`

## Azure public-demo completion

- Replaced the incomplete Render/Vercel runtime with a full-stack Azure VM deployment.
- VM: `airguard-demo`, Ubuntu 24.04, Standard B2as v2, Azure for Students.
- Public URL: `https://airguard-074-demo-2302.indonesiacentral.cloudapp.azure.com`.
- Deployed revision: `9c5ef06` from branch `Canh`; the same commit is on the team repository and deployment mirror.
- Runtime directory: `/home/azureuser/airguard-core`.
- Protected environment file: `/home/azureuser/airguard-demo.env` with mode `600`; secrets were generated on the VM and not printed or committed.

### Final implementation changes

- `docker-compose.public-demo.yml`: added one-shot `db-migrate`, mounted migrations read-only, and gated backend startup on successful migration completion.
- `backend/app/services/prophet_forecast_service.py`: removed the unsupported claim that the lowest forecast point is automatically suitable for outdoor activity; the summary now discloses simulator/baseline status and requires current alert/profile checks.
- `tests/test_backend/test_prophet_forecast.py`: added safety wording assertions.
- `docs/environment-setup.md`: documented the public-demo migration command.

### Verification evidence

- Initial and incremental Docker builds completed successfully.
- `db-migrate` exited `0`; authentication, reporting, station/alert UTF-8 and demo-user migrations completed idempotently.
- Public `/health` returned `ok`; `/ready` returned database `ok`.
- Stations endpoint returned exactly S01-S05; all five were online, fresh and labeled `source=simulator`.
- History, alerts, AQI forecast and spatial heatmap returned HTTP 200.
- Forecast returned three horizons and the deployed raw response contains the simulator/baseline disclaimer without the prior unsafe phrase.
- Agent UTF-8 query for current S03 data routed to `get_location_environment`; evidence and map action targeted `poi_ngoc_trai_lake` with AQI/PM2.5 evidence.
- HTTPS certificate was issued successfully by Let's Encrypt.
- Docker service is enabled and active. All eight long-running containers use `restart=unless-stopped`.
- Host listening-port check exposed only 22, 80 and 443; PostgreSQL 5432 and MQTT 1883 remain internal.
- Target forecast test: 3 passed. Public Compose validation: passed.
- UTF-8 integration test collection on the Windows host was blocked by missing local `argon2`; the Azure backend image includes and starts with that dependency.

### Remaining operational notes

- `OPENAI_API_KEY` is intentionally blank, so the Agent uses deterministic grounded behavior rather than an external LLM.
- Azure automatic shutdown is disabled. Availability still depends on remaining Azure for Students credit and the VM not being manually stopped.
- SSH port 22 remains public; restrict the Azure NSG source to the operator's current IP after deployment access is no longer needed.

## Azure auto-deploy completion

- Added `.github/workflows/deploy-azure.yml`, `scripts/deploy-azure-vm.sh` and `docs/azure-auto-deploy.md`.
- Pushes to `Canh` are sent to both the private team repository and `zangzang1303/airguard-core` by the local `origin` push URLs.
- The deploy job is scoped to the deployment mirror because the current GitHub account has `WRITE` rather than `ADMIN` permission on the team repository.
- Repository secret `AZURE_DEPLOY_SSH_KEY` was created in `zangzang1303/airguard-core` after explicit user approval.
- The VM authorized-key entry uses `restrict` and forced command `/usr/local/sbin/airguard-deploy`; arbitrary SSH commands were verified to fail.
- The workflow sends a Git bundle for the exact commit. The root-owned wrapper verifies bundle head/SHA, requires a fast-forward update, refuses a dirty checkout, serializes deployments with `flock`, runs Compose and checks public readiness.
- Manual forced-command bundle test deployed `a960bd5` successfully.
- GitHub Actions run `32627347754` completed successfully on the first real push.
- Upgraded to `actions/checkout@v6`; final run `32627407531` completed all seven deployment/readiness steps successfully in 28 seconds.
- VM final revision is `9c5ef06`; public `/backend/ready` reports database `ok`.
- The active restricted key count is one and the revoked v1 key count is zero on the VM.
- The active v2 private/public key files were removed from the workstation after the successful run. Two inaccessible v1 test files remain under the Windows Temp directory, but their public key was revoked from the VM and cannot authenticate.
