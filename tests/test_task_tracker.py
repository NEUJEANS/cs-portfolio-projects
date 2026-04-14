from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "projects" / "task-tracker-cli" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from task_tracker_cli.cli import main
from task_tracker_cli.repository import TaskRepository
from task_tracker_cli.service import TaskService


class TaskTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_file = Path(self.temp_dir.name) / "tasks.json"
        self.repository = TaskRepository(self.data_file)
        self.service = TaskService(self.repository)

    def run_cli(self, *args: str) -> tuple[int, str]:
        buffer = io.StringIO()
        previous = os.environ.get("TASK_TRACKER_DATA_FILE")
        os.environ["TASK_TRACKER_DATA_FILE"] = str(self.data_file)
        try:
            with redirect_stdout(buffer):
                code = main(list(args))
        finally:
            if previous is None:
                os.environ.pop("TASK_TRACKER_DATA_FILE", None)
            else:
                os.environ["TASK_TRACKER_DATA_FILE"] = previous
        return code, buffer.getvalue()

    def test_add_and_list_open_tasks(self) -> None:
        created = self.service.add_task("Write report")
        self.assertEqual(created.id, 1)

        tasks = self.service.list_tasks(status="open")
        self.assertEqual([task.title for task in tasks], ["Write report"])
        self.assertFalse(tasks[0].completed)

    def test_mark_done_and_stats(self) -> None:
        self.service.add_task("Finish lab")
        self.service.add_task("Review notes")
        self.service.mark_done(1)

        stats = self.service.stats()
        self.assertEqual((stats.total, stats.open, stats.completed), (2, 1, 1))

    def test_delete_task_removes_it(self) -> None:
        self.service.add_task("Draft README")
        deleted = self.service.delete_task(1)
        self.assertEqual(deleted.title, "Draft README")
        self.assertEqual(self.service.list_tasks(), [])

    def test_empty_existing_data_file_is_treated_as_no_tasks(self) -> None:
        self.data_file.write_text("", encoding="utf-8")
        code, output = self.run_cli("add", "Recovered from empty file")
        self.assertEqual(code, 0)
        self.assertIn("Added task 1", output)

    def test_cli_happy_path(self) -> None:
        code, output = self.run_cli("add", "Study graphs")
        self.assertEqual(code, 0)
        self.assertIn("Added task 1", output)

        code, output = self.run_cli("done", "1")
        self.assertEqual(code, 0)
        self.assertIn("Completed task 1", output)

        code, output = self.run_cli("stats")
        self.assertEqual(code, 0)
        self.assertIn("Completed: 1", output)

    def test_cli_empty_list_message(self) -> None:
        code, output = self.run_cli("list", "--status", "open")
        self.assertEqual(code, 0)
        self.assertIn("No tasks found.", output)

    def test_rejects_blank_title(self) -> None:
        code, output = self.run_cli("add", "   ")
        self.assertEqual(code, 1)
        self.assertIn("Task title cannot be empty", output)


if __name__ == "__main__":
    unittest.main()
