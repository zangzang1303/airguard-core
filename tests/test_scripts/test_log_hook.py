import importlib.util
from pathlib import Path


def load_log_hook_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "log_hook.py"
    spec = importlib.util.spec_from_file_location("log_hook", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_codex_normalize_reads_prompt_from_transcript(tmp_path, monkeypatch):
    module = load_log_hook_module()
    transcript_file = tmp_path / "transcript.jsonl"
    transcript_file.write_text(
        '{"role": "user", "content": "Xin chao tu transcript"}\n',
        encoding="utf-8",
    )

    def fake_git(command: str) -> str:
        if command == "git remote get-url origin":
            return "https://github.com/example/P-074.git"
        if command == "git rev-parse --abbrev-ref HEAD":
            return "main"
        if command == "git rev-parse --short HEAD":
            return "abc1234"
        if command == "git config user.email":
            return "student@example.com"
        return ""

    monkeypatch.setattr(module, "git", fake_git)

    entry = module.normalize(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "session-1",
            "model": "gpt-5.4-mini",
            "turn_id": "turn-1",
            "transcript_path": str(transcript_file),
        },
        "codex",
    )

    assert entry is not None
    assert entry["repo"] == "P-074"
    assert entry["prompt"] == "Xin chao tu transcript"
    assert entry["transcript_path"] == str(transcript_file)


def test_terminal_transcript_prompt_is_ignored(tmp_path, monkeypatch):
    module = load_log_hook_module()

    def fake_git(command: str) -> str:
        if command == "git remote get-url origin":
            return "https://github.com/example/P-074.git"
        if command == "git rev-parse --abbrev-ref HEAD":
            return "main"
        if command == "git rev-parse --short HEAD":
            return "abc1234"
        if command == "git config user.email":
            return "student@example.com"
        return ""

    monkeypatch.setattr(module, "git", fake_git)

    entry = module.normalize(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "session-2",
            "model": "",
            "prompt": (
                "PS E:\\Vinproject\\P-074> ruff check src/ tests/ --fix\n"
                ">> ruff format src/ tests/\n"
                "Found 1 error (1 fixed, 0 remaining)."
            ),
        },
        "copilot",
    )

    assert entry is None
