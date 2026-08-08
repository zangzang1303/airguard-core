#!/usr/bin/env python3
"""Submit local AI usage logs to the grading server.

The live file is atomically rotated to a uniquely-named pending file before
network I/O. Pending files are durable work items: a failed or interrupted run
leaves them in place, and the next run resumes them before processing new logs.
Only entries acknowledged by the server are appended to the archive.
"""

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
<<<<<<< HEAD
# test
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
=======


def _load_local_env() -> None:
    """Load .env even when the lightweight hook Python lacks python-dotenv."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        env_file = Path.cwd() / ".env"
        if not env_file.exists():
            return
        try:
            lines = env_file.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            return
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            if stripped.startswith("export "):
                stripped = stripped[7:].lstrip()
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if key:
                os.environ.setdefault(key, value)
    else:
        load_dotenv()


_load_local_env()
>>>>>>> 56319bf357b88155f831ce2c008dba10fdc1e2d7

SERVER_URL = os.environ.get("AI_LOG_SERVER", "")
API_KEY = os.environ.get("AI_LOG_API_KEY", "")
LOG_DIR = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
LOG_FILE = LOG_DIR / "session.jsonl"
ARCHIVE_DIR = LOG_DIR / "archive"

# Match the server-side maximum while draining every batch in one invocation.
BATCH_LIMIT = 500
SUBMIT_LOCK_STALE_SECONDS = 15 * 60


def _with_newline(line: str) -> str:
    return line if line.endswith("\n") else line + "\n"


def _append_lines(path: Path, lines: list[str]) -> None:
    """Append complete JSONL records without overwriting prior history."""
    if not lines:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as dst:
        dst.writelines(_with_newline(line) for line in lines)


def _archive_lines(lines: list[str]) -> None:
    """Archive only records that the server has acknowledged."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _append_lines(ARCHIVE_DIR / f"{today}.jsonl", lines)


def _quarantine_lines(lines: list[str]) -> None:
    """Preserve malformed input separately instead of silently deleting it."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _append_lines(ARCHIVE_DIR / f"invalid-{today}.jsonl", lines)


def _rewrite_pending(pending: Path, lines: list[str]) -> None:
    """Atomically replace a pending file with its unsubmitted remainder."""
    if not lines:
        pending.unlink(missing_ok=True)
        return

    tmp = pending.with_name(
        f"{pending.name}.tmp.{os.getpid()}.{time.time_ns()}"
    )
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.writelines(_with_newline(line) for line in lines)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, pending)
    finally:
        tmp.unlink(missing_ok=True)


def _read_pending(pending: Path) -> tuple[list[tuple[dict, str]], list[str]]:
    valid: list[tuple[dict, str]] = []
    invalid: list[str] = []
    with open(pending, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                invalid.append(line)
                continue
            if not isinstance(entry, dict):
                invalid.append(line)
                continue
            if not entry.get("entry_id"):
                # Older hook records predate entry IDs. Derive one from the
                # immutable raw record so network retries stay idempotent.
                digest = hashlib.sha256(
                    stripped.encode("utf-8")
                ).hexdigest()
                entry["entry_id"] = f"legacy-{digest}"
                line = json.dumps(entry, ensure_ascii=False) + "\n"
            valid.append((entry, line))
    return valid, invalid


def _post_entries(entries: list[dict]) -> int:
    payload = json.dumps(
        {"entries": entries}, ensure_ascii=False
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    req = urllib.request.Request(
        SERVER_URL,
        data=payload,
        headers=headers,
        method="POST",
<<<<<<< HEAD
    )  

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[ai-log] Submitted {len(entries)} entries → {resp.status}", file=sys.stderr)
    except (urllib.error.URLError, TimeoutError) as e:
        # Failure: restore the whole pending (including leftover) for next push.
        _restore_pending(pending)
        print(f"[ai-log] Submit failed: {e} — logs kept locally.", file=sys.stderr)
        sys.exit(0)  # Don't block push on server error
=======
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status

>>>>>>> 56319bf357b88155f831ce2c008dba10fdc1e2d7

def _process_pending(pending: Path) -> bool:
    """Drain one durable pending file, returning False on any retryable error."""
    while pending.exists():
        try:
            records, invalid_lines = _read_pending(pending)
        except OSError as exc:
            print(
                f"[ai-log] Cannot read {pending.name}: {exc}", file=sys.stderr
            )
            return False

        if invalid_lines:
            try:
                _quarantine_lines(invalid_lines)
                _rewrite_pending(pending, [line for _, line in records])
            except OSError as exc:
                print(
                    f"[ai-log] Cannot quarantine malformed logs: {exc}",
                    file=sys.stderr,
                )
                return False
            print(
                f"[ai-log] Quarantined {len(invalid_lines)} malformed "
                "record(s).",
                file=sys.stderr,
            )

        if not records:
            pending.unlink(missing_ok=True)
            return True

        batch = records[:BATCH_LIMIT]
        entries = [entry for entry, _ in batch]
        batch_lines = [line for _, line in batch]

        try:
            status = _post_entries(entries)
        except (OSError, urllib.error.URLError) as exc:
            print(
                f"[ai-log] Submit failed: {exc} — {pending.name} retained.",
                file=sys.stderr,
            )
            return False

        # Archive before removing the acknowledged records. If archival fails,
        # retrying is safe because every newly-created entry has a stable ID.
        try:
            _archive_lines(batch_lines)
            remaining = [line for _, line in records[BATCH_LIMIT:]]
            _rewrite_pending(pending, remaining)
        except OSError as exc:
            print(
                f"[ai-log] Server accepted the batch but local rotation "
                f"failed: {exc}. The batch will be retried by ID.",
                file=sys.stderr,
            )
            return False

        print(
            f"[ai-log] Submitted {len(entries)} entries → {status}",
            file=sys.stderr,
        )

    return True


def _acquire_submit_lock() -> tuple[int, Path] | None:
    """Prevent two pushes from rotating/submitting the same files at once."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    lock_file = LOG_DIR / "submit.lock"

    for _ in range(2):
        try:
            fd = os.open(
                lock_file,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            try:
                age = time.time() - lock_file.stat().st_mtime
            except FileNotFoundError:
                continue
            if age <= SUBMIT_LOCK_STALE_SECONDS:
                return None
            try:
                lock_file.unlink()
            except FileNotFoundError:
                continue
        else:
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
            return fd, lock_file
    return None


def _release_submit_lock(lock: tuple[int, Path]) -> None:
    fd, lock_file = lock
    os.close(fd)
    lock_file.unlink(missing_ok=True)


def _rotate_live_file() -> Path | None:
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        return None
    pending = LOG_FILE.with_name(
        f"session.pending.{time.time_ns()}.{os.getpid()}.jsonl"
    )
    os.replace(LOG_FILE, pending)
    return pending


def main() -> int:
    if not SERVER_URL:
        print(
            "[ai-log] AI_LOG_SERVER is not configured; refusing to silently "
            "skip submission.",
            file=sys.stderr,
        )
        return 1

    lock = _acquire_submit_lock()
    if lock is None:
        print(
            "[ai-log] Another submission is already running.", file=sys.stderr
        )
        return 1

    try:
        try:
            _rotate_live_file()
        except OSError as exc:
            print(f"[ai-log] Cannot rotate live log: {exc}", file=sys.stderr)
            return 1

        pending_files = sorted(LOG_DIR.glob("session.pending.*.jsonl"))
        if not pending_files:
            print("[ai-log] No logs to submit.", file=sys.stderr)
            return 0

        for pending in pending_files:
            if not _process_pending(pending):
                return 1
        return 0
    finally:
        _release_submit_lock(lock)


if __name__ == "__main__":
    raise SystemExit(main())
