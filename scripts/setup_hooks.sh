#!/usr/bin/env bash
# Install the AI-log pre-push hook without discarding an existing user hook.
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOK_PATH=$(git rev-parse --git-path hooks/pre-push)
case "$HOOK_PATH" in
  /*|[A-Za-z]:/*) HOOK_FILE="$HOOK_PATH" ;;
  *) HOOK_FILE="$REPO_ROOT/$HOOK_PATH" ;;
esac
USER_HOOK="$HOOK_FILE.user"
MARKER="# AI_LOG_HOOK_V2"

mkdir -p "$(dirname "$HOOK_FILE")"
cd "$REPO_ROOT"

if [ -f "$HOOK_FILE" ] && ! grep -Fq "$MARKER" "$HOOK_FILE"; then
  if grep -Fq "scripts/log_antigravity.py" "$HOOK_FILE" \
      && grep -Fq "scripts/submit_log.py" "$HOOK_FILE"; then
    echo "[ai-log] Upgrading legacy AI-log pre-push hook."
  else
    if [ -e "$USER_HOOK" ]; then
      echo "[ai-log] Refusing to overwrite existing backup: $USER_HOOK" >&2
      exit 1
    fi
    mv "$HOOK_FILE" "$USER_HOOK"
    chmod +x "$USER_HOOK" 2>/dev/null || true
    echo "[ai-log] Preserved existing pre-push hook as $USER_HOOK"
  fi
fi

cat > "$HOOK_FILE" <<'EOF'
#!/usr/bin/env bash
# AI_LOG_HOOK_V2
set -u

REPO_ROOT=$(git rev-parse --show-toplevel) || exit 1
cd "$REPO_ROOT" || exit 1
USER_HOOK=$(git rev-parse --git-path hooks/pre-push.user)

if [ -f "$USER_HOOK" ]; then
  chmod +x "$USER_HOOK" 2>/dev/null || true
  "$USER_HOOK" "$@" || exit $?
fi

bash scripts/_pyrun.sh scripts/log_antigravity.py --auto || exit $?
bash scripts/_pyrun.sh scripts/submit_log.py || exit $?
EOF

chmod +x "$HOOK_FILE"
chmod +x scripts/_pyrun.sh 2>/dev/null || true
mkdir -p .ai-log
touch .ai-log/.gitkeep

echo "[ai-log] Git pre-push hook installed. Logging errors will block the push."
echo "[ai-log] Configure AI_LOG_SERVER and AI_LOG_API_KEY in .env."
