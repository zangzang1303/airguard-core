#!/usr/bin/env bash
set -euo pipefail

readonly REPO_DIR="/home/azureuser/airguard-core"
readonly ENV_FILE="/home/azureuser/airguard-demo.env"
readonly COMPOSE_FILE="docker-compose.public-demo.yml"
readonly PUBLIC_READY_URL="https://airguard-074-app.indonesiacentral.cloudapp.azure.com/backend/ready"

if [[ "${SSH_ORIGINAL_COMMAND:-}" =~ ^deploy[[:space:]]([0-9a-f]{40})$ ]]; then
  readonly TARGET_COMMIT="${BASH_REMATCH[1]}"
else
  echo "This SSH key only accepts: deploy <40-character-commit-sha>."
  exit 64
fi

readonly BUNDLE_PATH="$(mktemp /tmp/airguard-deploy.XXXXXX.bundle)"
trap 'rm -f "$BUNDLE_PATH"' EXIT

cat > "$BUNDLE_PATH"

exec 9>"/tmp/airguard-deploy.lock"
if ! flock -n 9; then
  echo "Another AirGuard deployment is already running."
  exit 75
fi

cd "$REPO_DIR"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Refusing to deploy over a dirty VM checkout."
  exit 1
fi

git bundle verify "$BUNDLE_PATH"
bundle_commit="$(git bundle list-heads "$BUNDLE_PATH" refs/heads/airguard-deploy | awk '{print $1}')"
if [[ "$bundle_commit" != "$TARGET_COMMIT" ]]; then
  echo "Bundle commit does not match the requested deployment commit."
  exit 65
fi

git fetch "$BUNDLE_PATH" refs/heads/airguard-deploy
current_commit="$(git rev-parse HEAD)"
if ! git merge-base --is-ancestor "$current_commit" "$TARGET_COMMIT"; then
  echo "Refusing a non-fast-forward deployment."
  exit 1
fi
git merge --ff-only "$TARGET_COMMIT"

docker compose \
  --env-file "$ENV_FILE" \
  -f "$COMPOSE_FILE" \
  up -d --build --remove-orphans

docker compose \
  --env-file "$ENV_FILE" \
  -f "$COMPOSE_FILE" \
  ps

curl \
  --fail \
  --silent \
  --show-error \
  --retry 12 \
  --retry-delay 5 \
  --retry-all-errors \
  --max-time 10 \
  "$PUBLIC_READY_URL"

echo
echo "AirGuard deployment completed at commit $(git rev-parse --short HEAD)."
