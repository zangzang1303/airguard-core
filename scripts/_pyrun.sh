#!/usr/bin/env bash
# Cross-platform Python launcher for AI log hooks.
# Prefers the project's virtual environment, then tries system interpreters.
# Git Bash launched by hooks can have a stripped PATH, so Windows install
# locations remain a final fallback.
# Designed to be sourced or called as: bash scripts/_pyrun.sh <script> [args...]
#
# Fails loudly if no working Python is found. Silent success would make the
# project claim that logs were captured when no logger ever ran.
set -u

SCRIPT_PATH=$0
case "$SCRIPT_PATH" in
  */*) SCRIPT_PARENT=${SCRIPT_PATH%/*} ;;
  *) SCRIPT_PARENT=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_PARENT" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

is_working_python() {
  "$1" -c "import sys" >/dev/null 2>&1
}

for cand in \
  "$REPO_ROOT/.venv/bin/python" \
  "$REPO_ROOT/.venv/Scripts/python.exe" \
  "${HOME:-}/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"; do
  if [ -x "$cand" ] && is_working_python "$cand"; then
    exec "$cand" "$@"
  fi
done

if command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
  exec py -3 "$@"
fi

for name in python3 python; do
  if command -v "$name" >/dev/null 2>&1 && is_working_python "$name"; then
    exec "$name" "$@"
  fi
done

# PATH lookup failed — probe standard Windows install locations.
shopt -s nullglob 2>/dev/null || true
for cand in \
  /c/Users/*/AppData/Local/Programs/Python/Python*/python.exe \
  "/c/Program Files/Python"*/python.exe \
  "/c/Program Files (x86)/Python"*/python.exe \
  /c/Python*/python.exe; do
  if [ -x "$cand" ] && is_working_python "$cand"; then
    exec "$cand" "$@"
  fi
done
shopt -u nullglob 2>/dev/null || true

echo "[ai-log] No working Python interpreter found. Recreate .venv or install Python 3.11+." >&2
exit 127
