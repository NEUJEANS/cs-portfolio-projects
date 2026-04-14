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
        add = self.run_cli("add", "Prepare demo", "--priority", "high", "--due", "2026-04-20", "--tag", "school")
        self.assertEqual(add.returncode, 0)
        self.assertIn("Added:", add.stdout)
        self.assertIn("Prepare demo", add.stdout)
        self.assertIn("tags=school", add.stdout)

        listed = self.run_cli("list")
        self.assertEqual(listed.returncode, 0)
        self.assertIn("Prepare demo", listed.stdout)
        self.assertIn("todo", listed.stdout)
        self.assertIn("school", listed.stdout)

    def test_done_and_filtering(self) -> None:
        self.run_cli("add", "Finish docs", "--tag", "writing")
        done = self.run_cli("done", "1")
        self.assertEqual(done.returncode, 0)
        self.assertIn("Completed task #1", done.stdout)

        done_list = self.run_cli("list", "--status", "done")
        self.assertIn("Finish docs", done_list.stdout)

        todo_list = self.run_cli("list", "--status", "todo")
        self.assertIn("No tasks found.", todo_list.stdout)

    def test_search_and_tag_filters(self) -> None:
        self.run_cli("add", "Ship OS project", "--tag", "school", "--tag", "demo")
        self.run_cli("add", "Buy milk", "--tag", "personal")

        filtered = self.run_cli("list", "--search", "project", "--tag", "school")
        self.assertEqual(filtered.returncode, 0)
        self.assertIn("Ship OS project", filtered.stdout)
        self.assertNotIn("Buy milk", filtered.stdout)

    def test_update_tags_and_clear_tags(self) -> None:
        self.run_cli("add", "Draft README", "--tag", "draft")
        updated = self.run_cli("update", "1", "--tag", "portfolio", "--tag", "writing")
        self.assertEqual(updated.returncode, 0)
        self.assertIn("tags=portfolio,writing", updated.stdout)

        cleared = self.run_cli("update", "1", "--clear-tags")
        self.assertEqual(cleared.returncode, 0)
        self.assertIn("tags=-", cleared.stdout)

    def test_update_rejects_conflicting_tag_flags(self) -> None:
        self.run_cli("add", "Draft README", "--tag", "draft")
        result = self.run_cli("update", "1", "--tag", "portfolio", "--clear-tags")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Use either --tag or --clear-tags", result.stderr)

    def test_missing_task_returns_error(self) -> None:
        result = self.run_cli("done", "999")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Task 999 was not found", result.stderr)

    def test_blank_title_is_rejected(self) -> None:
        result = self.run_cli("add", "   ")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Description cannot be empty", result.stderr)

    def test_invalid_tag_is_rejected(self) -> None:
        result = self.run_cli("add", "Bad tags", "--tag", "bad!")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Tags may only contain", result.stderr)


if __name__ == "__main__":
    unittest.main()
