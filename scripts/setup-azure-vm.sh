#!/usr/bin/env bash
# =============================================================================
# AirGuard AI — Azure VM First-Time Setup
# Run this script ONCE on the Azure VM as azureuser.
# After setup, all subsequent deploys happen automatically via GitHub Actions
# when code is pushed to branch: Canh
#
# Usage:
#   ssh azureuser@airguard-074-app.indonesiacentral.cloudapp.azure.com
#   bash setup-azure-vm.sh
# =============================================================================
set -euo pipefail

REPO_DIR="/home/azureuser/airguard-core"
ENV_FILE="/home/azureuser/airguard-demo.env"
DEPLOY_SCRIPT_TARGET="/home/azureuser/bin/deploy"

# ---------------------------------------------------------------------------
# 1. Clone repo (chi lan dau)
# ---------------------------------------------------------------------------
if [[ ! -d "$REPO_DIR/.git" ]]; then
  echo ">>> Cloning repository..."
  git clone https://github.com/AI20K-Build-Phase-Cohort-3/P-074.git "$REPO_DIR"
else
  echo ">>> Repo already exists at $REPO_DIR, skipping clone."
fi

# ---------------------------------------------------------------------------
# 2. Create deploy script wrapper (forced SSH command handler)
#    The GitHub Actions workflow sends: ssh ... "deploy <sha>"
#    authorized_keys will force this binary to be executed.
# ---------------------------------------------------------------------------
echo ">>> Installing deploy script wrapper..."
mkdir -p /home/azureuser/bin
cp "$REPO_DIR/scripts/deploy-azure-vm.sh" "$DEPLOY_SCRIPT_TARGET"
chmod 755 "$DEPLOY_SCRIPT_TARGET"

# ---------------------------------------------------------------------------
# 3. Create production .env file
#    EDIT THE VALUES BELOW before running this script!
# ---------------------------------------------------------------------------
echo ">>> Creating $ENV_FILE..."

cat > "$ENV_FILE" <<'ENVEOF'
# AirGuard AI -- Production Environment (Azure VM)
# DO NOT commit this file. It lives only on the server.

DEMO_DOMAIN=airguard-074-app.indonesiacentral.cloudapp.azure.com
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD

# CORS -- must match the public URL
CORS_ORIGINS=https://airguard-074-app.indonesiacentral.cloudapp.azure.com

# Frontend URL (used for email links, OAuth redirect)
FRONTEND_URL=https://airguard-074-app.indonesiacentral.cloudapp.azure.com

# Google OAuth (optional -- leave blank to use demo login)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://airguard-074-app.indonesiacentral.cloudapp.azure.com/backend/api/v1/auth/google/callback
COOKIE_SECURE=true
COOKIE_SAMESITE=lax

# Demo login mode (keep true for MVP demo)
AUTH_DEMO_MODE=true

# AI Agent LLM -- pick ONE provider
LLM_PROVIDER=auto
OPENAI_API_KEY=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash

# Email notifications (optional)
NOTIFICATION_PROVIDER=disabled
RESEND_API_KEY=
RESEND_FROM_EMAIL=
RESEND_FROM_NAME=AirGuard AI
RESEND_REPLY_TO=

# Sensor & alert defaults (safe to leave as-is)
SENSOR_SCENARIO=normal
SENSOR_RANDOM_SEED=740
STALE_AFTER_SECONDS=300
AQI_WARNING_THRESHOLD=101
AQI_CRITICAL_THRESHOLD=151
CO2_WARNING_THRESHOLD=1000
CO2_CRITICAL_THRESHOLD=1500
NOISE_DB_WARNING_THRESHOLD=70
NOISE_DB_CRITICAL_THRESHOLD=85
TEMPERATURE_WARNING_THRESHOLD=35
TEMPERATURE_CRITICAL_THRESHOLD=39
VENTILATION_TRIGGER_SECONDS=30
ENVEOF

echo ">>> IMPORTANT: Edit $ENV_FILE and set POSTGRES_PASSWORD and API keys!"
echo ""

# ---------------------------------------------------------------------------
# 4. Show the SSH public key to add to GitHub Secrets
# ---------------------------------------------------------------------------
echo ">>> Checking deploy SSH key..."
if [[ ! -f /home/azureuser/.ssh/airguard_deploy ]]; then
  echo ">>> Generating deploy SSH key pair..."
  ssh-keygen -t ed25519 -f /home/azureuser/.ssh/airguard_deploy -N "" -C "airguard-github-actions-deploy"
fi

echo ""
echo "============================================================"
echo "STEP A: Add PUBLIC key to authorized_keys (with forced command)"
echo "============================================================"
PUBKEY=$(cat /home/azureuser/.ssh/airguard_deploy.pub)
echo ""
echo "Run:"
echo "echo 'command=\"/home/azureuser/bin/deploy\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ${PUBKEY}' >> /home/azureuser/.ssh/authorized_keys"
echo ""

echo "============================================================"
echo "STEP B: Add PRIVATE key to GitHub Secrets"
echo "  Repo Settings -> Secrets -> Actions -> New secret"
echo "  Name: AZURE_DEPLOY_SSH_KEY"
echo "  Value: (paste below)"
echo "============================================================"
cat /home/azureuser/.ssh/airguard_deploy
echo ""

echo "============================================================"
echo "STEP C: Verify host fingerprint in deploy-azure.yml"
echo "  Current server fingerprint:"
echo "============================================================"
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256
echo ""
echo "Compare with EXPECTED_HOST_FINGERPRINT in .github/workflows/deploy-azure.yml"
echo ""

echo "============================================================"
echo "STEP D: Azure NSG -- Ensure ports are OPEN"
echo "  Port 80 (HTTP - Caddy ACME + redirect)"
echo "  Port 443 (HTTPS)"
echo "  BLOCK: 5432, 1883, 8000, 8001 (Docker internal only)"
echo "============================================================"
echo ""
echo "Setup complete. Push to branch 'Canh' to trigger auto-deploy."
echo "Or: GitHub -> Actions -> 'Deploy Azure demo' -> Run workflow"
