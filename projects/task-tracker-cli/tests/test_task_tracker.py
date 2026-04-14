import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.task_tracker import TaskService, TaskStorage, TaskTrackerError


class TaskServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "tasks.json"
        self.service = TaskService(TaskStorage(self.data_file))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_task_persists_metadata(self):
        task = self.service.add_task(
            "Ship portfolio slice",
            priority="high",
            due_date="2026-04-20",
            tags=["School", "demo"],
        )
        self.assertEqual(task.id, 1)
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.due_date, "2026-04-20")
        self.assertEqual(task.tags, ["school", "demo"])

        payload = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(payload[0]["description"], "Ship portfolio slice")
        self.assertEqual(payload[0]["tags"], ["school", "demo"])

    def test_update_and_summary(self):
        self.service.add_task("A", tags=["class"])
        self.service.add_task("B", priority="low")
        self.service.set_status(1, "in-progress")
        self.service.set_status(2, "done")

        summary = self.service.summary()
        self.assertEqual(summary["todo"], 0)
        self.assertEqual(summary["in-progress"], 1)
        self.assertEqual(summary["done"], 1)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["tagged"], 1)
        self.assertEqual(summary["unique_tags"], 1)

    def test_list_tasks_can_sort_by_due_date(self):
        self.service.add_task("No due date")
        self.service.add_task("Soon", due_date="2026-04-16")
        self.service.add_task("Later", due_date="2026-04-18")

        tasks = self.service.list_tasks(sort_by="due_date")
        self.assertEqual([task.description for task in tasks], ["Soon", "Later", "No due date"])

    def test_list_tasks_can_search_and_filter_by_tag(self):
        self.service.add_task("Prepare operating systems demo", tags=["school", "demo"])
        self.service.add_task("Buy groceries", tags=["personal"])
        self.service.add_task("Finish demo script", tags=["demo"])

        search_results = self.service.list_tasks(search="operating")
        self.assertEqual([task.description for task in search_results], ["Prepare operating systems demo"])

        tag_results = self.service.list_tasks(tags=["demo"])
        self.assertEqual([task.description for task in tag_results], ["Prepare operating systems demo", "Finish demo script"])

        combined_results = self.service.list_tasks(search="school", tags=["demo"])
        self.assertEqual([task.description for task in combined_results], ["Prepare operating systems demo"])

    def test_update_tags_can_replace_or_clear(self):
        self.service.add_task("Prepare slides", tags=["draft"])

        updated = self.service.update_task(1, tags=["presentation", "school"])
        self.assertEqual(updated.tags, ["presentation", "school"])

        cleared = self.service.update_task(1, tags=[])
        self.assertEqual(cleared.tags, [])

    def test_export_tasks_supports_csv_and_markdown(self):
        self.service.add_task("Prepare demo", priority="high", due_date="2026-04-16", tags=["demo", "school"])
        self.service.add_task("Write docs", tags=["docs"])

        tasks = self.service.list_tasks(sort_by="priority")
        csv_output = self.service.export_tasks(tasks, "csv")
        rows = list(csv.DictReader(io.StringIO(csv_output)))
        self.assertEqual(rows[0]["description"], "Prepare demo")
        self.assertEqual(rows[0]["tags"], "demo,school")

        markdown_output = self.service.export_tasks(tasks, "markdown")
        self.assertIn("# Task Export", markdown_output)
        self.assertIn("| 1 | Prepare demo | todo | high | 2026-04-16 | demo, school |", markdown_output)

    def test_delete_missing_task_raises_error(self):
        with self.assertRaises(TaskTrackerError):
            self.service.delete_task(99)

    def test_update_requires_valid_due_date(self):
        self.service.add_task("A")
        with self.assertRaises(TaskTrackerError):
            self.service.update_task(1, due_date="04-20-2026")

    def test_invalid_tag_characters_raise_error(self):
        with self.assertRaises(TaskTrackerError):
            self.service.add_task("A", tags=["bad!"])


class TaskCliSmokeTests(unittest.TestCase):
    def test_cli_add_search_update_export_and_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "tasks.json"
            export_file = Path(temp_dir) / "tasks.md"
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
                    "--tag",
                    "School",
                    "--tag",
                    "demo,portfolio",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(add_result.returncode, 0, add_result.stdout + add_result.stderr)
            self.assertIn("tags=school,demo,portfolio", add_result.stdout)

            list_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "list",
                    "--search",
                    "portfolio",
                    "--json",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(list_result.returncode, 0, list_result.stdout + list_result.stderr)
            self.assertIn('"tags": [', list_result.stdout)

            update_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "update",
                    "1",
                    "--tag",
                    "refined",
                    "--tag",
                    "backend",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(update_result.returncode, 0, update_result.stdout + update_result.stderr)
            self.assertIn("tags=refined,backend", update_result.stdout)

            export_stdout_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "export",
                    "--format",
                    "csv",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(export_stdout_result.returncode, 0, export_stdout_result.stdout + export_stdout_result.stderr)
            self.assertIn("description,status,priority", export_stdout_result.stdout)

            export_file_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "export",
                    "--format",
                    "markdown",
                    "--output",
                    str(export_file),
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(export_file_result.returncode, 0, export_file_result.stdout + export_file_result.stderr)
            self.assertTrue(export_file.exists())
            self.assertIn("# Task Export", export_file.read_text(encoding="utf-8"))

            summary_result = subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "summary", "--json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(summary_result.returncode, 0, summary_result.stdout + summary_result.stderr)
            self.assertIn('"tagged": 1', summary_result.stdout)
            self.assertIn('"unique_tags": 2', summary_result.stdout)


if __name__ == "__main__":
    unittest.main()
