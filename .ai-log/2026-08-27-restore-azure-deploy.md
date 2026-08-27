# AI Work Log

## Date / agent / machine

2026-08-27 / Codex / local workspace

## Goal

Restore the prior Azure deployment path for the `Canh` branch and deploy it to the public demo URL.

## Context read

`AGENTS.md`, the historical Azure workflow at commit `a960bd5`, and its public Compose topology.

## Files changed

Restored the Azure workflow, the public Compose/Caddy production topology, and the frontend production image configuration.

## Decisions and rationale

The restored deployment commit contains only production delivery configuration; application source remains at the `main`-equivalent `Canh` commit selected by the user.

## Commands/tests run and results

`docker compose -f docker-compose.public-demo.yml config --quiet` passed with non-secret validation values. Docker emitted a local credential-config access warning only.

## Contracts/risks changed

The Azure VM needs its existing `AZURE_DEPLOY_SSH_KEY` repository secret and `/home/azureuser/airguard-demo.env`. These values are intentionally not stored in Git.

## Next exact step

Commit and push the deploy configuration to `Canh`; monitor the GitHub Actions deployment and public readiness endpoint.
