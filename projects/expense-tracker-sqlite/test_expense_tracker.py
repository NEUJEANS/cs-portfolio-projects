import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from expense_tracker import ExpenseTracker


class ExpenseTrackerTests(unittest.TestCase):
    def test_add_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            tracker.add('food', 12.5, 'lunch', '2026-04-10')
            tracker.add('food', 7.5, 'coffee', '2026-04-11')
            tracker.add('transport', 3.0, 'bus', '2026-04-11')
            summary = tracker.total_by_category()
            self.assertEqual(summary[0]['category'], 'food')
            self.assertEqual(summary[0]['total'], 20.0)
            self.assertEqual(summary[0]['entry_count'], 2)

    def test_list_filters_by_category_and_date_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            tracker.add('Food', 12.5, spent_on='2026-04-10')
            tracker.add('food', 8.0, spent_on='2026-04-15')
            tracker.add('transport', 4.0, spent_on='2026-04-16')
            rows = tracker.list(category='FOOD', start_date='2026-04-11', end_date='2026-04-30')
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['amount'], 8.0)

    def test_monthly_summary_groups_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            tracker.add('food', 10, spent_on='2026-03-30')
            tracker.add('food', 15, spent_on='2026-04-01')
            tracker.add('rent', 500, spent_on='2026-04-02')
            summary = tracker.total_by_month(start_date='2026-04-01', end_date='2026-04-30')
            self.assertEqual(summary, [
                {'month': '2026-04', 'total': 515.0, 'entry_count': 2},
            ])

    def test_rejects_non_positive_amount_and_invalid_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            with self.assertRaises(ValueError):
                tracker.add('food', 0)
            with self.assertRaises(ValueError):
                tracker.add('food', 5, spent_on='2026-14-01')

    def test_migrates_existing_database_without_spent_on_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            with tracker._connect() as conn:
                conn.execute('DROP TABLE expenses')
                conn.execute('CREATE TABLE expenses (id INTEGER PRIMARY KEY, category TEXT, amount REAL, note TEXT)')
                conn.execute('INSERT INTO expenses(category, amount, note) VALUES (?, ?, ?)', ('food', 12.5, 'legacy'))
            migrated = ExpenseTracker(db)
            rows = migrated.list()
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]['spent_on'])

    def test_cli_supports_filtered_listing_and_monthly_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            project_dir = Path(__file__).parent
            commands = [
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'add', 'food', '12.50', '--note', 'lunch', '--date', '2026-04-10'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'add', 'rent', '700', '--date', '2026-05-01'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'list', '--category', 'FOOD', '--start-date', '2026-04-01', '--end-date', '2026-04-30'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'summary', '--group-by', 'month', '--start-date', '2026-04-01', '--end-date', '2026-04-30'],
            ]
            for command in commands[:2]:
                subprocess.run(command, cwd=project_dir, check=True, capture_output=True, text=True)
            listing = subprocess.run(commands[2], cwd=project_dir, check=True, capture_output=True, text=True)
            summary = subprocess.run(commands[3], cwd=project_dir, check=True, capture_output=True, text=True)
            self.assertIn('2026-04-10 food $12.50 lunch', listing.stdout)
            self.assertIn('2026-04: $12.50 (1 entries)', summary.stdout)
            self.assertNotIn('2026-05', summary.stdout)

    def test_cli_returns_clean_error_for_invalid_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            project_dir = Path(__file__).parent
            result = subprocess.run(
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'add', 'food', '-2'],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('error: amount must be greater than 0', result.stderr or result.stdout)


if __name__ == '__main__':
    unittest.main()
