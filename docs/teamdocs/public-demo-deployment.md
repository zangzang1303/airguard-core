# Deploy a public AirGuard demo

This deployment is for an MVP simulator demo, not an official air-quality
monitoring service.  The dashboard must keep its simulator label and must not
be presented as certified live environmental data.

## Prerequisites

- A Linux VPS with Docker Engine and Docker Compose installed (2 GB RAM or
  more is recommended).
- A DNS name with an `A` record pointing to the VPS public IP.  Cloudflare DNS
  is supported, but its proxy is optional.
- Ports 80 and 443 permitted by the VPS firewall/security group.

## Server setup

Clone the repository on the VPS. Create a server-only environment file outside
the repository, for example `/opt/airguard-demo.env`:

```env
DEMO_DOMAIN=airguard.example.com
POSTGRES_PASSWORD=replace-with-a-long-random-password
OPENAI_API_KEY=
MODEL_NAME=gpt-4o-mini
SENSOR_SCENARIO=normal
```

`OPENAI_API_KEY` is optional only when the Agent-chat capability is not being
demonstrated. Never put this file in Git or expose it in browser variables.

Start the stack:

```bash
docker compose --env-file /opt/airguard-demo.env -f docker-compose.public-demo.yml up -d --build
docker compose --env-file /opt/airguard-demo.env -f docker-compose.public-demo.yml ps
curl -fsS https://airguard.example.com/backend/health
```

Caddy automatically obtains and renews TLS certificates after the DNS record
resolves to the VPS. Only Caddy publishes Internet-facing ports. PostgreSQL,
MQTT, FastAPI and the Agent remain private to the Docker network.

## Update and rollback

```bash
git pull
docker compose --env-file /opt/airguard-demo.env -f docker-compose.public-demo.yml up -d --build
docker compose --env-file /opt/airguard-demo.env -f docker-compose.public-demo.yml logs --tail=100 caddy backend frontend
```

Use a tagged Git revision before each demo so a rollback is a deliberate
checkout followed by the same `up -d --build` command. Do not delete the
`postgres_data` volume during an update.
