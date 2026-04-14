import tempfile, unittest
from pathlib import Path
from task_tracker import TaskTracker

class TaskTrackerTests(unittest.TestCase):
    def test_add_complete_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'tasks.json'
            tracker = TaskTracker(path)
            task = tracker.add('study graphs', 'high')
            self.assertEqual(len(tracker.list()), 1)
            tracker.complete(task['id'])
            self.assertTrue(tracker.list()[0]['done'])
            tracker.remove(task['id'])
            self.assertEqual(tracker.list(), [])

if __name__ == '__main__':
    unittest.main()
