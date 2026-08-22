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

if [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
elif command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
  PY=python3
elif command -v py >/dev/null 2>&1 && py -3 --version >/dev/null 2>&1; then
  PY="py -3"
else
  # PATH lookup failed — probe standard Windows install locations.
  PY=""
  shopt -s nullglob 2>/dev/null || true
  for cand in \
    /c/Users/*/AppData/Local/Programs/Python/Python*/python.exe \
    "/c/Program Files/Python"*/python.exe \
    "/c/Program Files (x86)/Python"*/python.exe \
    /c/Python*/python.exe; do
    if [ -x "$cand" ]; then PY="$cand"; break; fi
  done
  shopt -u nullglob 2>/dev/null || true
  [ -n "$PY" ] || exit 0
fi






# shellcheck disable=SC2086
exec $PY "$@"
