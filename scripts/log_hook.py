#!/usr/bin/env python3
"""
Shared AI hook logger — works with Claude Code, Gemini CLI, Codex, Cursor, Copilot.
Reads JSON from stdin, normalizes to common format, appends to .ai-log/session.jsonl
"""
import json
import os
import re
import sys
import subprocess
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))
MAX_STRUCTURED_PAYLOAD = 4000
_SENSITIVE_KEY_RE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|secret|"
    r"password|authorization|cookie)",
    re.IGNORECASE,
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|token|secret|"
    r"password|authorization)\b(\s*[:=]\s*)([^\s,;]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")


def git(cmd):
    try:
        return subprocess.check_output(
            cmd.split(), shell=False, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def _repo_name(origin: str) -> str:
    tail = origin.rstrip("/\\").replace("\\", "/").rsplit("/", 1)[-1]
    # Also support scp-style remotes such as git@host:owner/repo.git.
    tail = tail.rsplit(":", 1)[-1]
    return tail[:-4] if tail.endswith(".git") else tail


def _safe_text(value, limit: int) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = _BEARER_RE.sub("Bearer [REDACTED]", value)
    value = _SECRET_ASSIGNMENT_RE.sub(r"\1\2[REDACTED]", value)
    return value[:limit]


def _sanitize_payload(value, limit: int = MAX_STRUCTURED_PAYLOAD):
    """Redact credential-like fields and cap nested hook payloads."""

    def walk(item, depth: int = 0):
        if depth >= 6:
            return "[TRUNCATED_DEPTH]"
        if isinstance(item, dict):
            cleaned = {}
            for index, (key, child) in enumerate(item.items()):
                if index >= 50:
                    cleaned["_truncated_items"] = True
                    break
                key_text = str(key)
                cleaned[key_text] = (
                    "[REDACTED]"
                    if _SENSITIVE_KEY_RE.search(key_text)
                    else walk(child, depth + 1)
                )
            return cleaned
        if isinstance(item, (list, tuple)):
            cleaned = [walk(child, depth + 1) for child in item[:50]]
            if len(item) > 50:
                cleaned.append("[TRUNCATED_ITEMS]")
            return cleaned
        if isinstance(item, str):
            return _safe_text(item, 1000)
        if item is None or isinstance(item, (bool, int, float)):
            return item
        return _safe_text(item, 1000)

    cleaned = walk(value)
    encoded = json.dumps(cleaned, ensure_ascii=False, default=str)
    if len(encoded) <= limit:
        return cleaned
    return {"_truncated": True, "preview": encoded[:limit]}


def detect_tool(data: dict) -> str:
    """Detect which AI tool sent this hook event.

    Priority:
      1. --tool=NAME CLI argument (cross-platform: works in cmd.exe, PowerShell, bash)
      2. AI_TOOL_NAME env var (legacy, bash-only when set inline)
      3. Heuristics from payload shape
    """
    for arg in sys.argv[1:]:
        if arg.startswith("--tool="):
            return arg.split("=", 1)[1].lower()
    tool_env = os.environ.get("AI_TOOL_NAME", "").lower()
    if tool_env:
        return tool_env
    # Heuristics
    if "transcript_path" in data:
        return "codex"
    if data.get("hook_event_name", "").startswith(("Before", "After", "Session", "Pre", "Notification")):
        return "gemini"
    if data.get("hook_event_name", "")[0:1].islower():
        # camelCase event names → Cursor or Copilot
        if "workspace_roots" in data:
            return "cursor"
        if "toolName" in data:
            return "copilot"
    if "hook_event_name" in data:
        return "claude"
    return "unknown"


def normalize(data: dict, tool: str) -> dict | None:
    """Normalize tool-specific payload to common log entry."""
    event = data.get("hook_event_name") or data.get("event", "")
    ts = datetime.now(VN_TZ).isoformat()

    # Resolve repo from git origin. When cwd is not a git working tree (or
    # origin isn't set), skip the event entirely — these entries can't be
    # tied back to a team on the server and would just clutter the pending
    # queue forever.
    origin = git("git remote get-url origin")
    if not origin:
        return None
    repo = _repo_name(origin)

    base = {
        "ts": ts,
        "entry_id": f"hook-{uuid.uuid4()}",
        "tool": tool,
        "event": event,
        "session_id": (
            data.get("session_id") or
            data.get("conversation_id") or
            data.get("generation_id") or ""
        ),
        "model": data.get("model", ""),
        "repo": repo,
        "branch": git("git rev-parse --abbrev-ref HEAD"),
        "commit": git("git rev-parse --short HEAD"),
        "student": git("git config user.email"),
    }

    if tool == "claude":
        prompt = ""
        # UserPromptSubmit: prompt is at top level
        if event == "UserPromptSubmit":
            prompt = _safe_text(data.get("prompt", ""), 1000)
        # PostToolUse: extract from tool_input
        elif isinstance(data.get("tool_input"), dict):
            prompt = _safe_text(
                data["tool_input"].get("prompt")
                or data["tool_input"].get("content")
                or "",
                1000,
            )
        base.update({
            "prompt": prompt,
            "tool_name": data.get("tool_name", ""),
            "tool_input": (
                _sanitize_payload(data.get("tool_input"))
                if event != "UserPromptSubmit" and data.get("tool_input")
                else None
            ),
            "tool_response": (
                _sanitize_payload(data.get("tool_response"), 1000)
                if data.get("tool_response")
                else None
            ),
        })

    elif tool == "gemini":
        if event == "BeforeAgent":
            prompt = _safe_text(data.get("prompt", ""), 1000)
            base.update({"prompt": prompt})
        else:
            req = data.get("request", {})
            contents = req.get("contents", [])
            prompt = ""
            for c in reversed(contents):
                for part in c.get("parts", []):
                    if part.get("text"):
                        prompt = _safe_text(part["text"], 1000)
                        break
                if prompt:
                    break
            resp = data.get("response", {})
            answer = ""
            try:
                answer = _safe_text(
                    resp["candidates"][0]["content"]["parts"][0]["text"],
                    500,
                )
            except Exception:
                pass
            base.update({"prompt": prompt, "response_summary": answer})

    elif tool == "codex":
        base.update({
            "prompt": _safe_text(data.get("prompt", ""), 1000),
            "turn_id": data.get("turn_id", ""),
            "transcript_path": data.get("transcript_path", ""),
        })

    elif tool == "cursor":
        base.update({
            "prompt": _safe_text(data.get("prompt", ""), 1000),
            "files_context": _sanitize_payload(data.get("attachments", [])),
        })

    elif tool == "copilot":
        base.update({
            "prompt": _safe_text(data.get("prompt", ""), 1000),
            "tool_name": data.get("toolName", ""),
            "tool_args": (
                _sanitize_payload(data.get("toolArgs"))
                if data.get("toolArgs")
                else None
            ),
        })

    # Skip only true noise: no prompt AND no tool-specific payload (tool_input,
    # response_summary, tool_response, tool_args, files_context). Previously
    # this only checked `prompt`, which dropped Claude Bash/Edit events (their
    # tool_input has `command` / `file_path`, not `prompt` or `content`) and
    # any Gemini/Cursor/Copilot turn that carried context but no plain prompt.
    _PAYLOAD_KEYS = ("prompt", "tool_input", "response_summary",
                     "tool_response", "tool_args", "files_context")
    has_payload = any(base.get(k) for k in _PAYLOAD_KEYS)
    if not has_payload:
        return None

    return base


def main():
    # Read stdin as UTF-8 explicitly. On Windows, sys.stdin defaults to the
    # system code page (e.g. cp1252), which corrupts non-Latin1 prompts
    # (Vietnamese, CJK, emoji) into mojibake. The hook payload is always UTF-8.
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace").strip()
    if not raw:
        print("[ai-log] Hook supplied an empty payload.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[ai-log] Invalid hook JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    tool = detect_tool(data)
    entry = normalize(data, tool)
    if not entry:
        sys.exit(0)

    log_dir = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "session.jsonl"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Output valid JSON (required by some tools like Gemini)
    print(json.dumps({"status": "logged"}))


if __name__ == "__main__":
    main()
