#!/usr/bin/env python3
"""
Manual AI usage logger for web tools without automatic hook integration.

Usage (interactive):
  python scripts/log_manual.py

Usage (one-line):
  python scripts/log_manual.py --tool "chatgpt" --prompt "Asked ChatGPT to explain transformer architecture" --model "gpt-5.4"

Examples:
  # Tiến logs a ChatGPT session
  python scripts/log_manual.py --tool chatgpt --prompt "Brainstorm UI layout for /ai page"

  # Hoàng logs a Gemini web session
  python scripts/log_manual.py --tool gemini-web --prompt "Research risk scoring algorithms"

  # Quick interactive mode
  python scripts/log_manual.py
"""
import json
import os
import sys
import subprocess
import argparse
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))


def git(cmd):
    try:
        return subprocess.check_output(cmd.split(), shell=False, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def repo_name(origin: str) -> str:
    tail = origin.rstrip("/\\").replace("\\", "/").rsplit("/", 1)[-1]
    tail = tail.rsplit(":", 1)[-1]
    return tail[:-4] if tail.endswith(".git") else tail


def interactive_mode():
    """Prompt user for log info interactively."""
    print("\n📝 Manual AI Log Entry")
    print("=" * 40)

    tool = input("Tool name (e.g. chatgpt, gemini-web, copilot, other): ").strip()
    if not tool:
        tool = "unknown"

    model = input("Model (e.g. gpt-5.4, gemini-3-pro, skip to use tool name): ").strip()
    if not model:
        model = tool

    prompt = input("What did you ask/do? (brief summary): ").strip()
    if not prompt:
        print("[log] ❌ Prompt cannot be empty.", file=sys.stderr)
        sys.exit(1)

    result = input("Result/outcome (optional, press Enter to skip): ").strip()

    return tool, model, prompt, result


def main():
    parser = argparse.ArgumentParser(description="Manual AI usage logger")
    parser.add_argument("--tool", help="AI tool name (e.g. chatgpt, gemini-web)")
    parser.add_argument("--prompt", help="What you asked/did")
    parser.add_argument("--model", help="Model used (optional)")
    parser.add_argument("--result", help="Outcome/result (optional)", default="")
    args = parser.parse_args()

    if args.tool and args.prompt:
        tool = args.tool
        model = args.model or args.tool
        prompt = args.prompt
        result = args.result
    else:
        tool, model, prompt, result = interactive_mode()

    ts = datetime.now(VN_TZ).isoformat()

    student = git("git config user.email")
    if not student:
        student = os.environ.get("USERNAME", os.environ.get("USER", "unknown"))
        print(f"[log] ⚠️  git email not set! Using fallback: {student}", file=sys.stderr)
        print(f"[log] Run: git config user.email \"your@vinuni.edu.vn\"", file=sys.stderr)

    entry = {
        "ts": ts,
        "tool": tool,
        "event": "ManualLog",
        "entry_id": f"manual-{uuid.uuid4()}",
        "model": model,
        "repo": repo_name(git("git remote get-url origin")),
        "branch": git("git rev-parse --abbrev-ref HEAD"),
        "commit": git("git rev-parse --short HEAD"),
        "student": student,
        "prompt": prompt[:1000],
        "response_summary": result[:500] if result else "",
    }

    log_dir = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "session.jsonl"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\n[log] ✅ Logged: [{tool}] {prompt[:80]}")
    print(f"[log] 📁 Saved to: {log_file}")


if __name__ == "__main__":
    main()
