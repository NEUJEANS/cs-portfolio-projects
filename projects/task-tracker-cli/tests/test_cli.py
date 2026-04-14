from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TaskTrackerCliTests(unittest.TestCase):
    def run_cli(self, *args: str, db: Path) -> subprocess.CompletedProcess[str]:
        command = ["python3", "-m", "src.task_tracker_cli", "--db", str(db), *args]
        return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)

    def test_add_list_done_delete_summary_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db = Path(temp_dir) / "tasks.json"

            added = self.run_cli("add", "Write networks lab", "--priority", "high", "--due", "2026-04-20", db=db)
            self.assertEqual(added.returncode, 0, added.stderr)
            self.assertIn("Added task 1", added.stdout)

            listed = self.run_cli("list", "--status", "todo", db=db)
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("Write networks lab", listed.stdout)
            self.assertIn("priority=high", listed.stdout)

            completed = self.run_cli("done", "1", db=db)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Completed task 1", completed.stdout)

            summary = self.run_cli("summary", "--json", db=db)
            self.assertEqual(summary.returncode, 0, summary.stderr)
            payload = json.loads(summary.stdout)
            self.assertEqual(payload["done"], 1)
            self.assertEqual(payload["completion_rate"], 100.0)

            deleted = self.run_cli("delete", "1", db=db)
            self.assertEqual(deleted.returncode, 0, deleted.stderr)
            self.assertIn("Deleted task 1", deleted.stdout)

    def test_invalid_priority_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db = Path(temp_dir) / "tasks.json"
            result = self.run_cli("add", "Bad task", "--priority", "urgent", db=db)
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid priority", result.stderr)

    def test_json_listing_and_due_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db = Path(temp_dir) / "tasks.json"
            self.run_cli("add", "Soon task", "--due", "2026-04-15", db=db)
            self.run_cli("add", "Later task", "--due", "2026-04-25", db=db)

            result = self.run_cli("list", "--due-before", "2026-04-20", "--json", db=db)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["title"], "Soon task")


    def test_empty_title_and_missing_task_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db = Path(temp_dir) / "tasks.json"
            empty = self.run_cli("add", "   ", db=db)
            self.assertEqual(empty.returncode, 2)
            self.assertIn("task title cannot be empty", empty.stderr)

            missing = self.run_cli("done", "99", db=db)
            self.assertEqual(missing.returncode, 2)
            self.assertIn("task 99 not found", missing.stderr)

if __name__ == "__main__":
    unittest.main()
