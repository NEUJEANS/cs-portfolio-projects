import tempfile, unittest
from pathlib import Path
from expense_tracker import ExpenseTracker

class ExpenseTrackerTests(unittest.TestCase):
    def test_add_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            tracker.add('food', 12.5, 'lunch')
            tracker.add('food', 7.5, 'coffee')
            tracker.add('transport', 3.0, 'bus')
            summary = tracker.total_by_category()
            self.assertEqual(summary[0]['category'], 'food')
            self.assertEqual(summary[0]['total'], 20.0)

if __name__ == '__main__':
    unittest.main()
