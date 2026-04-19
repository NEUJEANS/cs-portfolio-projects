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

    def test_budget_status_reports_warning_and_overages_case_insensitively(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            tracker.add('Food', 40, spent_on='2026-04-05')
            tracker.add('food', 50, spent_on='2026-04-17')
            tracker.add('rent', 500, spent_on='2026-04-02')
            tracker.set_budget('food', 100, month='2026-04', alert_threshold=0.8)
            tracker.set_budget('rent', 450, month='2026-04', alert_threshold=0.9)

            rows = {row['category'].lower(): row for row in tracker.budget_status('2026-04')}

            self.assertEqual(rows['food']['spent'], 90.0)
            self.assertEqual(rows['food']['remaining'], 10.0)
            self.assertEqual(rows['food']['usage_percent'], 90.0)
            self.assertEqual(rows['food']['status'], 'warning')
            self.assertEqual(rows['food']['alert_threshold'], 80.0)

            self.assertEqual(rows['rent']['spent'], 500.0)
            self.assertEqual(rows['rent']['remaining'], -50.0)
            self.assertEqual(rows['rent']['status'], 'over')

    def test_budget_upsert_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            tracker.set_budget('food', 100, month='2026-04', alert_threshold=0.75)
            tracker.set_budget('FOOD', 120, month='2026-04', alert_threshold=0.9)

            budgets = tracker.list_budgets('2026-04')
            self.assertEqual(len(budgets), 1)
            self.assertEqual(budgets[0]['category'].lower(), 'food')
            self.assertEqual(budgets[0]['amount'], 120.0)
            self.assertEqual(budgets[0]['alert_threshold'], 0.9)

            with self.assertRaises(ValueError):
                tracker.set_budget('food', 100, month='2026-4', alert_threshold=0.8)
            with self.assertRaises(ValueError):
                tracker.set_budget('food', 100, month='2026-04', alert_threshold=1.5)

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

    def test_migrates_existing_budget_table_without_alert_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            tracker = ExpenseTracker(db)
            with tracker._connect() as conn:
                conn.execute('DROP TABLE budgets')
                conn.execute(
                    'CREATE TABLE budgets ('
                    'category TEXT NOT NULL COLLATE NOCASE, '
                    'month TEXT NOT NULL, '
                    'amount REAL NOT NULL, '
                    'PRIMARY KEY (category, month)'
                    ')'
                )
                conn.execute('INSERT INTO budgets(category, month, amount) VALUES (?, ?, ?)', ('food', '2026-04', 100))
            migrated = ExpenseTracker(db)
            budgets = migrated.list_budgets('2026-04')
            self.assertEqual(budgets, [
                {'category': 'food', 'month': '2026-04', 'amount': 100.0, 'alert_threshold': 0.8},
            ])

    def test_cli_supports_filtered_listing_monthly_summary_and_budget_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'expenses.db'
            project_dir = Path(__file__).parent
            commands = [
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'add', 'food', '40.00', '--date', '2026-04-05'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'add', 'food', '50.00', '--date', '2026-04-17'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'budget', 'set', 'food', '100', '--month', '2026-04', '--threshold', '0.8'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'list', '--category', 'FOOD', '--start-date', '2026-04-01', '--end-date', '2026-04-30'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'summary', '--group-by', 'month', '--start-date', '2026-04-01', '--end-date', '2026-04-30'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'budget', 'list', '--month', '2026-04'],
                [sys.executable, 'expense_tracker.py', '--db', str(db), 'budget', 'status', '--month', '2026-04'],
            ]
            for command in commands[:3]:
                subprocess.run(command, cwd=project_dir, check=True, capture_output=True, text=True)
            listing = subprocess.run(commands[3], cwd=project_dir, check=True, capture_output=True, text=True)
            summary = subprocess.run(commands[4], cwd=project_dir, check=True, capture_output=True, text=True)
            budget_list = subprocess.run(commands[5], cwd=project_dir, check=True, capture_output=True, text=True)
            budget_status = subprocess.run(commands[6], cwd=project_dir, check=True, capture_output=True, text=True)
            self.assertIn('2026-04-05 food $40.00', listing.stdout)
            self.assertIn('2026-04-17 food $50.00', listing.stdout)
            self.assertIn('2026-04: $90.00 (2 entries)', summary.stdout)
            self.assertIn('2026-04 food: $100.00 alert at 80.0%', budget_list.stdout)
            self.assertIn('food: $90.00 / $100.00 used (90.0%) [warning] $10.00 remaining', budget_status.stdout)

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
