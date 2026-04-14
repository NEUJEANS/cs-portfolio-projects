import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from library_manager import Library, LibraryError, main


class LibraryTests(unittest.TestCase):
    def make_library(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / 'library.db'
        return Library(db), db

    def test_add_checkout_return_and_clear_loan_metadata(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')

        due_day = lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 14))
        self.assertEqual(due_day.isoformat(), '2026-04-21')
        checked_out = lib.list_books()[0]
        self.assertFalse(checked_out['available'])
        self.assertEqual(checked_out['borrower'], 'Alex')
        self.assertEqual(checked_out['due_date'], '2026-04-21')

        lib.return_book(1)
        returned = lib.list_books()[0]
        self.assertTrue(returned['available'])
        self.assertIsNone(returned['borrower'])
        self.assertIsNone(returned['due_date'])

    def test_search_filters_by_title_or_author(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('The Pragmatic Programmer', 'Andrew Hunt')

        title_hits = lib.list_books(query='clean')
        author_hits = lib.list_books(query='hunt')

        self.assertEqual([row['title'] for row in title_hits], ['Clean Code'])
        self.assertEqual([row['title'] for row in author_hits], ['The Pragmatic Programmer'])

    def test_overdue_books_only_returns_past_due_loans(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 1))
        lib.checkout(2, 'Sam', loan_days=14, checkout_date=date(2026, 4, 10))

        overdue = lib.overdue_books(date(2026, 4, 15))
        self.assertEqual([row['title'] for row in overdue], ['Clean Code'])

    def test_rejects_invalid_checkout_and_return_transitions(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.checkout(1, 'Alex')

        with self.assertRaises(LibraryError):
            lib.checkout(1, 'Sam')
        with self.assertRaises(LibraryError):
            lib.return_book(99)
        with self.assertRaises(LibraryError):
            lib.add_book('   ', 'Robert C. Martin')

    def test_schema_migration_adds_new_columns_for_existing_databases(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / 'library.db'
        import sqlite3
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, available INTEGER DEFAULT 1)')

        Library(db)
        with sqlite3.connect(db) as conn:
            columns = {row[1] for row in conn.execute('PRAGMA table_info(books)')}
        self.assertTrue({'borrower', 'checked_out_at', 'due_date'}.issubset(columns))

    def test_cli_search_and_overdue_output(self):
        lib, db = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 1))

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(['--db', str(db), 'list', '--query', 'martin'])
        output = buffer.getvalue()
        self.assertIn('Clean Code', output)
        self.assertIn('Refactoring', output)

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(['--db', str(db), 'overdue', '--date', '2026-04-15'])
        overdue_output = buffer.getvalue()
        self.assertIn('checked out to Alex', overdue_output)
        self.assertNotIn('Refactoring', overdue_output)


if __name__ == '__main__':
    unittest.main()
