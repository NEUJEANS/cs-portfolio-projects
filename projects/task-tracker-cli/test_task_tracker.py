from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.task_tracker_cli.repository import TaskRepository
from src.task_tracker_cli.service import TaskService


class TaskTrackerTests(unittest.TestCase):
    def test_add_complete_remove(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'tasks.json'
            service = TaskService(TaskRepository(path))

            task = service.add_task('study graphs')
            self.assertEqual(len(service.list_tasks()), 1)

            completed = service.mark_done(task.id)
            self.assertTrue(completed.completed)
            self.assertTrue(service.list_tasks()[0].completed)

            deleted = service.delete_task(task.id)
            self.assertEqual(deleted.id, task.id)
            self.assertEqual(service.list_tasks(), [])


if __name__ == '__main__':
    unittest.main()
