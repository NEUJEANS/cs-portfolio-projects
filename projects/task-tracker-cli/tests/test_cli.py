from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


class TaskTrackerCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "tasks.json"
        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(SRC_DIR)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(self.env)
        return subprocess.run(
            [sys.executable, "-m", "task_tracker", "--db", str(self.db_path), *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_add_and_list_task(self) -> None:
        add = self.run_cli("add", "Prepare demo", "--priority", "high", "--due", "2026-04-20")
        self.assertEqual(add.returncode, 0)
        self.assertIn("Added:", add.stdout)
        self.assertIn("Prepare demo", add.stdout)

        listed = self.run_cli("list")
        self.assertEqual(listed.returncode, 0)
        self.assertIn("Prepare demo", listed.stdout)
        self.assertIn("todo", listed.stdout)

    def test_done_and_filtering(self) -> None:
        self.run_cli("add", "Finish docs")
        done = self.run_cli("done", "1")
        self.assertEqual(done.returncode, 0)
        self.assertIn("Completed task #1", done.stdout)

        done_list = self.run_cli("list", "--status", "done")
        self.assertIn("Finish docs", done_list.stdout)

        todo_list = self.run_cli("list", "--status", "todo")
        self.assertIn("No tasks found.", todo_list.stdout)

    def test_reopen_and_delete(self) -> None:
        self.run_cli("add", "Draft README")
        self.run_cli("done", "1")
        reopened = self.run_cli("reopen", "1")
        self.assertEqual(reopened.returncode, 0)
        self.assertIn("Reopened task #1", reopened.stdout)

        deleted = self.run_cli("delete", "1")
        self.assertEqual(deleted.returncode, 0)
        self.assertIn("Deleted task #1", deleted.stdout)

    def test_missing_task_returns_error(self) -> None:
        result = self.run_cli("done", "999")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Task 999 was not found", result.stderr)

    def test_blank_title_is_rejected(self) -> None:
        result = self.run_cli("add", "   ")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Description cannot be empty", result.stderr)


if __name__ == "__main__":
    unittest.main()
