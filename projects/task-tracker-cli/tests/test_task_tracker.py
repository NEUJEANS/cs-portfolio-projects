import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.task_tracker import TaskService, TaskStorage, TaskTrackerError


class TaskServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "tasks.json"
        self.service = TaskService(TaskStorage(self.data_file))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_task_persists_metadata(self):
        task = self.service.add_task("Ship portfolio slice", priority="high", due_date="2026-04-20")
        self.assertEqual(task.id, 1)
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.due_date, "2026-04-20")

        payload = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(payload[0]["description"], "Ship portfolio slice")

    def test_update_and_summary(self):
        self.service.add_task("A")
        self.service.add_task("B", priority="low")
        self.service.set_status(1, "in-progress")
        self.service.set_status(2, "done")

        summary = self.service.summary()
        self.assertEqual(summary["todo"], 0)
        self.assertEqual(summary["in-progress"], 1)
        self.assertEqual(summary["done"], 1)
        self.assertEqual(summary["total"], 2)

    def test_list_tasks_can_sort_by_due_date(self):
        self.service.add_task("No due date")
        self.service.add_task("Soon", due_date="2026-04-16")
        self.service.add_task("Later", due_date="2026-04-18")

        tasks = self.service.list_tasks(sort_by="due_date")
        self.assertEqual([task.description for task in tasks], ["Soon", "Later", "No due date"])

    def test_delete_missing_task_raises_error(self):
        with self.assertRaises(TaskTrackerError):
            self.service.delete_task(99)

    def test_update_requires_valid_due_date(self):
        self.service.add_task("A")
        with self.assertRaises(TaskTrackerError):
            self.service.update_task(1, due_date="04-20-2026")


class TaskCliSmokeTests(unittest.TestCase):
    def test_cli_add_and_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "tasks.json"
            project_dir = Path(__file__).resolve().parents[1]

            add_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "add",
                    "Prepare demo",
                    "--priority",
                    "high",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(add_result.returncode, 0, add_result.stdout + add_result.stderr)
            self.assertIn("Added:", add_result.stdout)

            summary_result = subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "summary"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(summary_result.returncode, 0, summary_result.stdout + summary_result.stderr)
            self.assertIn('"total": 1', summary_result.stdout)


if __name__ == "__main__":
    unittest.main()
