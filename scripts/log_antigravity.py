#!/usr/bin/env python3
"""
Antigravity IDE log scanner — extracts the exact user-typed prompts from
local Antigravity conversation transcripts.

Source of truth:
    ~/.gemini/antigravity-ide/brain/<conv_id>/.system_generated/logs/transcript.jsonl
    (with fallback to the legacy ~/.gemini/antigravity/brain/... layout)

Each transcript line is a JSON object. We emit one log entry per line where
`type == "USER_INPUT"` AND `source == "USER_EXPLICIT"`. The text inside
<USER_REQUEST>...</USER_REQUEST> is the exact prompt the student typed
(auxiliary <ADDITIONAL_METADATA> and <USER_SETTINGS_CHANGE> blocks are
stripped).

Why not other sources we considered?
  - ~/.gemini/antigravity-ide/conversations/<conv>.pb is encrypted.
  - brain/<conv>/task.md / walkthrough.md are AI-generated artifacts, not the
    user's prompt.
  - ~/.gemini/tmp/<slug>/chats/session-*.json is the Gemini CLI, not the
    Antigravity IDE.

Conversation → repo mapping
---------------------------
The brain folder has no .project_root file. We map a conv to the current repo
by scanning its transcript for tool-call `Cwd` values. A conversation counts
as belonging to this repo only when a tool ran at the repo root or inside it.

Usage:
  python scripts/log_antigravity.py --auto            # default: last 24h
  python scripts/log_antigravity.py --hours 72
  python scripts/log_antigravity.py --all             # every conv, no cutoff
  python scripts/log_antigravity.py --conv-id <id>    # one conversation
  python scripts/log_antigravity.py --dry-run         # preview only

Env overrides:
  ANTIGRAVITY_BRAIN_DIR  point at a different brain/ directory
  AI_LOG_DIR             where session.jsonl is written (default: .ai-log)
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Fix Windows console encoding so VN diacritics in prompts print cleanly.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VN_TZ = timezone(timedelta(hours=7))
GEMINI_HOME = Path.home() / ".gemini"

# Antigravity has shipped under two folder names; prefer the newer IDE one.
BRAIN_CANDIDATES = (
    GEMINI_HOME / "antigravity-ide" / "brain",
    GEMINI_HOME / "antigravity" / "brain",
)

USER_REQUEST_RE = re.compile(r"<USER_REQUEST>(.*?)</USER_REQUEST>", re.DOTALL)
AUX_BLOCK_RE = re.compile(
    r"<(?:ADDITIONAL_METADATA|USER_SETTINGS_CHANGE|SYSTEM_MESSAGE)>"
    r".*?"
    r"</(?:ADDITIONAL_METADATA|USER_SETTINGS_CHANGE|SYSTEM_MESSAGE)>",
    re.DOTALL,
)


def git(cmd: str) -> str:
    try:
        return subprocess.check_output(
            cmd.split(), shell=False, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def repo_name(origin: str) -> str:
    tail = origin.rstrip("/\\").replace("\\", "/").rsplit("/", 1)[-1]
    tail = tail.rsplit(":", 1)[-1]
    return tail[:-4] if tail.endswith(".git") else tail


# ---------------------------------------------------------------------------
# Locating brain/
# ---------------------------------------------------------------------------

def get_brain_dirs() -> list[Path]:
    """Brain directories to scan, newest layout first."""
    env = os.environ.get("ANTIGRAVITY_BRAIN_DIR")
    if env:
        p = Path(env)
        return [p] if p.exists() else []
    return [p for p in BRAIN_CANDIDATES if p.exists()]


# ---------------------------------------------------------------------------
# Path normalization + repo gating
# ---------------------------------------------------------------------------

def _normalize(p: str) -> str:
    """Normalize a local path without breaking case-sensitive platforms."""
    if not p:
        return ""
    normalized = os.path.normpath(p.strip()).replace("\\", "/").rstrip("/")
    return normalized.lower() if os.name == "nt" else normalized


def _unquote_arg(val):
    """Antigravity stores tool args as JSON-encoded strings. Unwrap them."""
    if not isinstance(val, str):
        return val
    val = val.strip()
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val[1:-1]
    return val


def _conv_cwds(transcript: Path) -> set[str]:
    """All Cwd values that appear in tool calls inside this transcript."""
    cwds: set[str] = set()
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for tc in (entry.get("tool_calls") or []):
                    args = tc.get("args") or {}
                    cwd = args.get("Cwd") or args.get("cwd")
                    cwd = _unquote_arg(cwd)
                    if isinstance(cwd, str):
                        n = _normalize(cwd)
                        if n:
                            cwds.add(n)
    except OSError:
        pass
    return cwds


def _conv_matches_repo(cwds: set[str], repo_root_n: str) -> bool:
    """True when a tool call ran in the repo or one of its descendants.

    Treating a parent directory as a match attributes the same conversation to
    every sibling repository below that parent, which can leak prompts across
    projects.
    """
    if not repo_root_n or not cwds:
        return False
    for cwd in cwds:
        if cwd == repo_root_n:
            return True
        if cwd.startswith(repo_root_n + "/"):
            return True
    return False


# ---------------------------------------------------------------------------
# Prompt extraction
# ---------------------------------------------------------------------------

def extract_user_prompt(content: str) -> str:
    """Pull the text between <USER_REQUEST>...</USER_REQUEST>. Fall back to
    stripping known auxiliary blocks if no wrapper is present."""
    if not isinstance(content, str):
        return ""
    m = USER_REQUEST_RE.search(content)
    if m:
        return m.group(1).strip()
    cleaned = AUX_BLOCK_RE.sub("", content)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Reading existing log to avoid duplicates
# ---------------------------------------------------------------------------

def get_logged_entry_ids(log_dir: Path) -> set[str]:
    """Read IDs from live, in-flight, and archived logs.

    Reading only session.jsonl causes every recently-scanned Antigravity prompt
    to be emitted again immediately after a successful rotation.
    """
    logged: set[str] = set()
    candidates = [log_dir / "session.jsonl"]
    candidates.extend(sorted(log_dir.glob("session.pending.*.jsonl")))
    candidates.extend(sorted((log_dir / "archive").glob("*.jsonl")))

    for log_file in candidates:
        if not log_file.exists():
            continue
        try:
            with open(log_file, encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    eid = entry.get("entry_id", "")
                    if eid:
                        logged.add(eid)
        except OSError:
            continue
    return logged


# ---------------------------------------------------------------------------
# Iterating user inputs
# ---------------------------------------------------------------------------

def iter_user_inputs(brain_dirs: list[Path], cutoff: datetime | None,
                     only_conv: str | None, repo_root_n: str):
    """Yield user-input dicts from every matching conversation transcript."""
    for brain in brain_dirs:
        for conv_dir in sorted(brain.iterdir()):
            if not conv_dir.is_dir():
                continue
            if only_conv and conv_dir.name != only_conv:
                continue
            transcript = (
                conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            )
            if not transcript.exists() or transcript.stat().st_size == 0:
                continue

            cwds = _conv_cwds(transcript)
            # If we have a repo root, skip convs that never touched it.
            if repo_root_n and not _conv_matches_repo(cwds, repo_root_n):
                continue

            with open(transcript, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if (entry.get("type") != "USER_INPUT"
                            or entry.get("source") != "USER_EXPLICIT"):
                        continue

                    ts = entry.get("created_at") or ""
                    if cutoff and ts:
                        try:
                            ts_dt = datetime.fromisoformat(
                                ts.replace("Z", "+00:00")
                            )
                            if ts_dt.tzinfo is None:
                                ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                            if ts_dt < cutoff:
                                continue
                        except (TypeError, ValueError):
                            continue

                    text = extract_user_prompt(entry.get("content", ""))
                    if len(text) < 2:
                        continue

                    try:
                        step_id = f"{int(entry.get('step_index', 0)):05d}"
                    except (TypeError, ValueError):
                        digest = hashlib.sha256(
                            f"{conv_dir.name}\0{ts}\0{text}".encode("utf-8")
                        ).hexdigest()[:16]
                        step_id = f"hash-{digest}"

                    yield {
                        "conv_id": conv_dir.name,
                        "step_id": step_id,
                        "timestamp": ts,
                        "text": text,
                    }


# ---------------------------------------------------------------------------
# Emitting entries
# ---------------------------------------------------------------------------

def build_entry(msg: dict, repo: str, branch: str, commit: str,
                student: str) -> dict:
    ts = msg["timestamp"]
    if ts.endswith("Z"):
        try:
            ts = (
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
                .astimezone(VN_TZ)
                .isoformat()
            )
        except ValueError:
            pass

    return {
        "ts": ts or datetime.now(VN_TZ).isoformat(),
        "tool": "antigravity",
        "event": "UserPrompt",
        "entry_id": f"antigravity-{msg['conv_id']}-{msg['step_id']}",
        "session_id": msg["conv_id"],
        "model": "gemini",
        "repo": repo,
        "branch": branch,
        "commit": commit,
        "student": student,
        "prompt": msg["text"],
        "response_summary": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract user prompts from Antigravity IDE transcripts"
                    " into .ai-log/session.jsonl."
    )
    parser.add_argument("--auto", action="store_true",
                        help="Default mode: scan recent conversations.")
    parser.add_argument("--hours", type=int, default=24,
                        help="Window in hours when scanning (default: 24).")
    parser.add_argument("--all", action="store_true",
                        help="Ignore the time window; scan everything.")
    parser.add_argument("--conv-id",
                        help="Limit to a single conversation id.")
    parser.add_argument("--no-repo-filter", action="store_true",
                        help="Don't filter conversations by current repo.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be logged, don't write.")
    # Parse legacy positional args only to provide a clear migration error.
    parser.add_argument("summary", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("model", nargs="?", help=argparse.SUPPRESS)
    args = parser.parse_args()

    # Legacy mode created synthetic TaskComplete records rather than real user
    # prompts. Refuse it instead of silently polluting the grading log.
    if args.summary and not (args.auto or args.conv_id or args.all):
        parser.error(
            "manual Antigravity logging is no longer supported; use --auto "
            "or scripts/log_manual.py for web-only tools"
        )

    brain_dirs = get_brain_dirs()
    if not brain_dirs:
        print("[antigravity-log] No Antigravity brain/ directory found "
              f"(checked {', '.join(str(p) for p in BRAIN_CANDIDATES)}).",
              file=sys.stderr)
        sys.exit(0)

    log_dir = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "session.jsonl"
    logged_ids = get_logged_entry_ids(log_dir)

    cutoff = None
    if not args.all and not args.conv_id:
        cutoff = datetime.now(tz=VN_TZ) - timedelta(hours=args.hours)

    repo_root = git("git rev-parse --show-toplevel") or str(Path.cwd())
    repo_root_n = "" if args.no_repo_filter else _normalize(repo_root)

    repo = repo_name(git("git remote get-url origin"))
    branch = git("git rev-parse --abbrev-ref HEAD")
    commit = git("git rev-parse --short HEAD")
    student = git("git config user.email") or os.environ.get(
        "USERNAME", os.environ.get("USER", "unknown"))

    new_entries: list[dict] = []
    for msg in iter_user_inputs(brain_dirs, cutoff, args.conv_id, repo_root_n):
        entry = build_entry(msg, repo or Path.cwd().name, branch, commit,
                            student)
        if entry["entry_id"] in logged_ids:
            continue
        new_entries.append(entry)
        logged_ids.add(entry["entry_id"])

    if not new_entries:
        scope = "all" if args.all else f"{args.hours}h"
        repo_note = "any repo" if args.no_repo_filter else f"repo={repo_root_n or '(unknown)'}"
        print(f"[antigravity-log] No new prompts ({repo_note}, window={scope}).",
              file=sys.stderr)
        sys.exit(0)

    if args.dry_run:
        print(f"\n[antigravity-log] DRY RUN — would log "
              f"{len(new_entries)} entries:\n")
        for e in new_entries:
            preview = e["prompt"].replace("\n", " ")[:120]
            print(f"  [{e['ts'][:19]}] {preview}")
        sys.exit(0)

    with open(log_file, "a", encoding="utf-8") as f:
        for e in new_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"[antigravity-log] Logged {len(new_entries)} prompt(s) from "
          f"Antigravity IDE.", file=sys.stderr)


if __name__ == "__main__":
    main()
