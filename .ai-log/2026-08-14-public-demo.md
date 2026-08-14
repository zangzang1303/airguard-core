# AI Work Log

## Date / agent / machine

2026-08-14 / Codex / local Windows workspace

## Goal

Prepare a secure, persistent public-demo deployment for AirGuard AI.

## Context read

`AGENTS.md`, `README.md`, `docs/environment-setup.md`, the existing Compose topology, Dockerfiles, frontend API client and `.gitignore`.

## Files changed

- `docker-compose.public-demo.yml`
- `infra/caddy/Caddyfile`
- `frontend/Dockerfile.production`
- `frontend/nginx.production.conf`
- `docs/public-demo-deployment.md`

## Decisions and rationale

Use a separate Compose file for public deployment so the local development topology remains unchanged. Caddy is the only Internet-facing service and terminates TLS; all backend, agent, database and MQTT traffic remains on the Docker network. The frontend uses `/backend` as its build-time API prefix, which Caddy strips before proxying to FastAPI.

## Commands/tests run and results

- `docker compose -f docker-compose.public-demo.yml config --quiet`: passed with temporary non-secret validation variables.
- `npx.cmd tsc --noEmit; npx.cmd vite build --outDir <temp>`: passed.
- The normal `npm run build` could not remove the pre-existing `frontend/dist` because a local process has it locked; it was not altered.

## Contracts/risks changed

No REST or MQTT contracts changed. This is a simulator-only MVP demo. A real public URL still requires a VPS/DNS domain or authenticated tunnel account and must use a server-only environment file containing a non-default database password.

## Blockers/open questions

No VPS, DNS name, or Cloudflare account access has been supplied, so deployment and public URL creation cannot be completed from this workspace.

## Next exact step

On the selected VPS, create `/opt/airguard-demo.env` as documented and run the Compose command in `docs/public-demo-deployment.md`.

## Handoff IDs (request/message/proposal/job)

None.
