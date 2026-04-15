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
            recurrence="weekly",
        )
        self.assertEqual(task.id, 1)
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.due_date, "2026-04-20")
        self.assertEqual(task.tags, ["school", "demo"])
        self.assertEqual(task.recurrence, "weekly")

        payload = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(payload[0]["description"], "Ship portfolio slice")
        self.assertEqual(payload[0]["tags"], ["school", "demo"])
        self.assertEqual(payload[0]["recurrence"], "weekly")

    def test_update_and_summary(self):
        self.service.add_task("A", tags=["class"], recurrence="daily", due_date="2026-04-20")
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
        self.assertEqual(summary["recurring"], 1)

    def test_completing_recurring_task_spawns_next_occurrence(self):
        self.service.add_task("Water plants", due_date="2026-01-31", recurrence="monthly", tags=["home"])

        completed, spawned = self.service.set_status(1, "done")

        self.assertEqual(completed.status, "done")
        self.assertIsNotNone(spawned)
        assert spawned is not None
        self.assertEqual(spawned.id, 2)
        self.assertEqual(spawned.status, "todo")
        self.assertEqual(spawned.due_date, "2026-02-28")
        self.assertEqual(spawned.recurrence, "monthly")
        self.assertEqual(spawned.tags, ["home"])

    def test_list_tasks_can_sort_by_due_date(self):
        self.service.add_task("No due date")
        self.service.add_task("Soon", due_date="2026-04-16")
        self.service.add_task("Later", due_date="2026-04-18")

        tasks = self.service.list_tasks(sort_by="due_date")
        self.assertEqual([task.description for task in tasks], ["Soon", "Later", "No due date"])

    def test_list_tasks_can_search_and_filter_by_tag(self):
        self.service.add_task("Prepare operating systems demo", tags=["school", "demo"], recurrence="weekly", due_date="2026-04-20")
        self.service.add_task("Buy groceries", tags=["personal"])
        self.service.add_task("Finish demo script", tags=["demo"])

        search_results = self.service.list_tasks(search="operating")
        self.assertEqual([task.description for task in search_results], ["Prepare operating systems demo"])

        tag_results = self.service.list_tasks(tags=["demo"])
        self.assertEqual([task.description for task in tag_results], ["Prepare operating systems demo", "Finish demo script"])

        recurrence_results = self.service.list_tasks(search="weekly")
        self.assertEqual([task.description for task in recurrence_results], ["Prepare operating systems demo"])

    def test_update_tags_can_replace_or_clear(self):
        self.service.add_task("Prepare slides", tags=["draft"], recurrence="weekly", due_date="2026-04-20")

        updated = self.service.update_task(1, tags=["presentation", "school"], recurrence="daily")
        self.assertEqual(updated.tags, ["presentation", "school"])
        self.assertEqual(updated.recurrence, "daily")

        cleared = self.service.update_task(1, tags=[], recurrence="")
        self.assertEqual(cleared.tags, [])
        self.assertIsNone(cleared.recurrence)

    def test_import_tasks_supports_csv_and_json(self):
        csv_file = Path(self.temp_dir.name) / "incoming.csv"
        csv_file.write_text(
            "description,status,priority,due_date,recurrence,tags\n"
            "Prepare slides,todo,high,2026-04-16,,\"demo,school\"\n"
            "Weekly sync,in-progress,medium,2026-04-18,weekly,team\n",
            encoding="utf-8",
        )

        imported_csv = self.service.import_tasks(csv_file, "csv")
        self.assertEqual(len(imported_csv), 2)
        self.assertEqual(imported_csv[0].id, 1)
        self.assertEqual(imported_csv[1].status, "in-progress")
        self.assertEqual(imported_csv[1].recurrence, "weekly")

        json_file = Path(self.temp_dir.name) / "incoming.json"
        json_file.write_text(
            json.dumps([
                {
                    "description": "Write recap",
                    "status": "done",
                    "priority": "low",
                    "tags": "docs,writing",
                }
            ]),
            encoding="utf-8",
        )

        imported_json = self.service.import_tasks(json_file, "json")
        self.assertEqual(len(imported_json), 1)
        self.assertEqual(imported_json[0].id, 3)
        self.assertEqual(imported_json[0].status, "done")
        self.assertEqual(imported_json[0].tags, ["docs", "writing"])

    def test_import_rejects_recurring_task_without_due_date(self):
        csv_file = Path(self.temp_dir.name) / "invalid.csv"
        csv_file.write_text(
            "description,status,priority,due_date,recurrence,tags\n"
            "Broken task,todo,medium,,weekly,ops\n",
            encoding="utf-8",
        )

        with self.assertRaises(TaskTrackerError):
            self.service.import_tasks(csv_file, "csv")

    def test_export_tasks_supports_csv_and_markdown(self):
        self.service.add_task(
            "Prepare demo",
            priority="high",
            due_date="2026-04-16",
            tags=["demo", "school"],
            recurrence="weekly",
        )
        self.service.add_task("Write docs", tags=["docs"])

        tasks = self.service.list_tasks(sort_by="priority")
        csv_output = self.service.export_tasks(tasks, "csv")
        rows = list(csv.DictReader(io.StringIO(csv_output)))
        self.assertEqual(rows[0]["description"], "Prepare demo")
        self.assertEqual(rows[0]["tags"], "demo,school")
        self.assertEqual(rows[0]["recurrence"], "weekly")

        markdown_output = self.service.export_tasks(tasks, "markdown")
        self.assertIn("# Task Export", markdown_output)
        self.assertIn("| 1 | Prepare demo | todo | high | 2026-04-16 | weekly | demo, school |", markdown_output)

    def test_archive_completed_tasks_writes_snapshot_and_prunes_store(self):
        self.service.add_task("Prepare demo", tags=["demo"])
        self.service.add_task("Ship docs", tags=["docs"])
        self.service.set_status(2, "done")

        archive_dir = Path(self.temp_dir.name) / "archives"
        snapshot = self.service.archive_completed_tasks(archive_dir)

        self.assertEqual([task.id for task in snapshot.archived_tasks], [2])
        self.assertTrue(snapshot.json_path.exists())
        self.assertTrue(snapshot.markdown_path.exists())

        json_payload = json.loads(snapshot.json_path.read_text(encoding="utf-8"))
        self.assertEqual(json_payload["archived_ids"], [2])
        self.assertEqual(json_payload["tasks"][0]["description"], "Ship docs")
        self.assertIn("# Completed Task Archive", snapshot.markdown_path.read_text(encoding="utf-8"))

        remaining = self.service.list_tasks()
        self.assertEqual([task.id for task in remaining], [1])
        self.assertEqual([task.id for task in snapshot.remaining_tasks], [1])

    def test_archive_keep_preserves_active_store(self):
        self.service.add_task("Prepare demo")
        self.service.set_status(1, "done")

        snapshot = self.service.archive_completed_tasks(keep=True)

        self.assertEqual(len(snapshot.archived_tasks), 1)
        self.assertEqual(len(self.service.list_tasks()), 1)
        self.assertEqual(self.service.list_tasks()[0].status, "done")

    def test_archive_requires_completed_tasks(self):
        self.service.add_task("Prepare demo")
        with self.assertRaises(TaskTrackerError):
            self.service.archive_completed_tasks()

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

    def test_recurrence_requires_due_date(self):
        with self.assertRaises(TaskTrackerError):
            self.service.add_task("A", recurrence="daily")


class TaskCliSmokeTests(unittest.TestCase):
    def test_cli_add_complete_export_archive_and_summary_with_recurring_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "tasks.json"
            export_file = Path(temp_dir) / "tasks.md"
            archive_dir = Path(temp_dir) / "archives"
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
                    "--due",
                    "2026-04-20",
                    "--repeat",
                    "weekly",
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
            self.assertIn("repeat=weekly", add_result.stdout)

            done_result = subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "done", "1"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(done_result.returncode, 0, done_result.stdout + done_result.stderr)
            self.assertIn("Spawned next recurring task", done_result.stdout)
            self.assertIn("due=2026-04-27", done_result.stdout)

            archive_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "archive",
                    "--output-dir",
                    str(archive_dir),
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(archive_result.returncode, 0, archive_result.stdout + archive_result.stderr)
            self.assertIn("Archived 1 completed task(s)", archive_result.stdout)
            self.assertIn("Remaining active tasks: 1", archive_result.stdout)
            self.assertTrue(list(archive_dir.glob("completed-*.json")))
            self.assertTrue(list(archive_dir.glob("completed-*.md")))

            list_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "list",
                    "--search",
                    "weekly",
                    "--json",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(list_result.returncode, 0, list_result.stdout + list_result.stderr)
            payload = json.loads(list_result.stdout)
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["status"], "todo")
            self.assertEqual(payload[0]["recurrence"], "weekly")

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
            self.assertIn("| 2 | Prepare demo | todo | high | 2026-04-27 | weekly | school, demo, portfolio |", export_file.read_text(encoding="utf-8"))

            summary_result = subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "summary", "--json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(summary_result.returncode, 0, summary_result.stdout + summary_result.stderr)
            self.assertIn('"recurring": 1', summary_result.stdout)
            self.assertIn('"done": 0', summary_result.stdout)

    def test_cli_clear_repeat_rejects_conflicting_flags(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "tasks.json"
            project_dir = Path(__file__).resolve().parents[1]
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "add",
                    "Task",
                    "--due",
                    "2026-04-20",
                    "--repeat",
                    "daily",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            conflict_result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "src.task_tracker",
                    "--data-file",
                    str(data_file),
                    "update",
                    "1",
                    "--repeat",
                    "weekly",
                    "--clear-repeat",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(conflict_result.returncode, 1)
            self.assertIn("Use either --repeat or --clear-repeat, not both.", conflict_result.stderr)

    def test_cli_archive_keep_retains_completed_tasks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "tasks.json"
            project_dir = Path(__file__).resolve().parents[1]
            subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "add", "Task"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "done", "1"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            archive_result = subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "archive", "--keep"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(archive_result.returncode, 0, archive_result.stdout + archive_result.stderr)
            self.assertIn("Completed tasks were kept in the active store.", archive_result.stdout)

            list_result = subprocess.run(
                ["python3", "-m", "src.task_tracker", "--data-file", str(data_file), "list", "--json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertIn('"status": "done"', list_result.stdout)


if __name__ == "__main__":
    unittest.main()
