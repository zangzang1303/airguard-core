import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import log_antigravity  # noqa: E402
import log_hook  # noqa: E402
import submit_log  # noqa: E402


def write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(entry) + "\n" for entry in entries),
        encoding="utf-8",
    )


class AntigravityLogTests(unittest.TestCase):
    def test_dedup_reads_live_pending_and_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            write_jsonl(log_dir / "session.jsonl", [{"entry_id": "live"}])
            write_jsonl(
                log_dir / "session.pending.1.jsonl",
                [{"entry_id": "pending"}],
            )
            write_jsonl(
                log_dir / "archive" / "2026-07-31.jsonl",
                [{"entry_id": "archived"}],
            )

            self.assertEqual(
                log_antigravity.get_logged_entry_ids(log_dir),
                {"live", "pending", "archived"},
            )

    def test_repo_filter_rejects_parent_and_sibling_directories(self):
        root = log_antigravity._normalize(r"D:\work\project-a")
        child = log_antigravity._normalize(r"D:\work\project-a\src")
        parent = log_antigravity._normalize(r"D:\work")
        sibling = log_antigravity._normalize(r"D:\work\project-b")

        self.assertTrue(log_antigravity._conv_matches_repo({root}, root))
        self.assertTrue(log_antigravity._conv_matches_repo({child}, root))
        self.assertFalse(log_antigravity._conv_matches_repo({parent}, root))
        self.assertFalse(log_antigravity._conv_matches_repo({sibling}, root))


class HookNormalizationTests(unittest.TestCase):
    @staticmethod
    def fake_git(command: str) -> str:
        return {
            "git remote get-url origin": "git@example.test:team/project.git",
            "git rev-parse --abbrev-ref HEAD": "feature/logging",
            "git rev-parse --short HEAD": "abc1234",
            "git config user.email": "student@example.test",
        }.get(command, "")

    def test_empty_lifecycle_event_is_dropped(self):
        with mock.patch.object(log_hook, "git", self.fake_git):
            entry = log_hook.normalize(
                {"hook_event_name": "AfterModel", "session_id": "session"},
                "gemini",
            )
        self.assertIsNone(entry)

    def test_payload_is_identified_bounded_and_redacted(self):
        data = {
            "hook_event_name": "PostToolUse",
            "session_id": "session",
            "tool_name": "Bash",
            "tool_input": {
                "api_key": "do-not-log-this",
                "command": "Authorization=Bearer very-secret-token",
                "content": "x" * 8000,
            },
        }
        with mock.patch.object(log_hook, "git", self.fake_git):
            entry = log_hook.normalize(data, "claude")

        self.assertIsNotNone(entry)
        self.assertTrue(entry["entry_id"].startswith("hook-"))
        serialized = json.dumps(entry["tool_input"])
        self.assertNotIn("do-not-log-this", serialized)
        self.assertNotIn("very-secret-token", serialized)
        self.assertLessEqual(len(serialized), log_hook.MAX_STRUCTURED_PAYLOAD + 100)


class SubmitLogTests(unittest.TestCase):
    def module_paths(self, tmp: str):
        log_dir = Path(tmp)
        return {
            "LOG_DIR": log_dir,
            "LOG_FILE": log_dir / "session.jsonl",
            "ARCHIVE_DIR": log_dir / "archive",
            "SERVER_URL": "https://example.test/ingest",
            "API_KEY": "test-key",
        }

    def test_drains_all_batches_and_archives_only_acknowledged_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.module_paths(tmp)
            entries = [{"value": index} for index in range(501)]
            write_jsonl(paths["LOG_FILE"], entries)
            batches: list[list[dict]] = []

            def fake_post(batch):
                batches.append(batch)
                return 201

            with mock.patch.multiple(submit_log, **paths), mock.patch.object(
                submit_log, "_post_entries", side_effect=fake_post
            ):
                result = submit_log.main()

            self.assertEqual(result, 0)
            self.assertEqual([len(batch) for batch in batches], [500, 1])
            self.assertTrue(
                all(entry.get("entry_id") for batch in batches for entry in batch)
            )
            archive_files = list(paths["ARCHIVE_DIR"].glob("2026-*.jsonl"))
            self.assertEqual(len(archive_files), 1)
            self.assertEqual(len(archive_files[0].read_text().splitlines()), 501)
            self.assertFalse(paths["LOG_FILE"].exists())
            self.assertEqual(
                list(paths["LOG_DIR"].glob("session.pending.*.jsonl")), []
            )

    def test_failed_submission_retains_orphaned_pending_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.module_paths(tmp)
            pending = paths["LOG_DIR"] / "session.pending.old.jsonl"
            write_jsonl(pending, [{"entry_id": "retry-me", "value": 1}])

            with mock.patch.multiple(submit_log, **paths), mock.patch.object(
                submit_log,
                "_post_entries",
                side_effect=urllib.error.URLError("offline"),
            ):
                result = submit_log.main()

            self.assertEqual(result, 1)
            self.assertTrue(pending.exists())
            self.assertEqual(
                json.loads(pending.read_text().strip())["entry_id"], "retry-me"
            )

    def test_malformed_records_are_quarantined(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.module_paths(tmp)
            paths["LOG_FILE"].parent.mkdir(parents=True, exist_ok=True)
            paths["LOG_FILE"].write_text(
                '{"entry_id":"valid"}\nnot-json\n', encoding="utf-8"
            )

            with mock.patch.multiple(submit_log, **paths), mock.patch.object(
                submit_log, "_post_entries", return_value=200
            ):
                result = submit_log.main()

            self.assertEqual(result, 0)
            invalid = list(paths["ARCHIVE_DIR"].glob("invalid-*.jsonl"))
            self.assertEqual(len(invalid), 1)
            self.assertEqual(invalid[0].read_text().strip(), "not-json")

    def test_builtin_env_loader_works_without_python_dotenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".env").write_text(
                'AI_LOG_TEST_FALLBACK="loaded"\n', encoding="utf-8"
            )
            with mock.patch.dict(os.environ, {}, clear=False), mock.patch.dict(
                sys.modules, {"dotenv": None}
            ), mock.patch("pathlib.Path.cwd", return_value=Path(tmp)):
                os.environ.pop("AI_LOG_TEST_FALLBACK", None)
                submit_log._load_local_env()
                self.assertEqual(os.environ["AI_LOG_TEST_FALLBACK"], "loaded")


if __name__ == "__main__":
    unittest.main()
