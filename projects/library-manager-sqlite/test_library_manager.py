import io
import sqlite3
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

    def test_auto_search_uses_full_text_prefix_matching_and_preview(self):
        lib, _ = self.make_library()
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')
        lib.add_book('Distributed Algorithms', 'Nancy Lynch')
        lib.add_book('Computer Networks', 'Andrew S. Tanenbaum')

        results = lib.list_books(query='distrib tanen')

        self.assertEqual([row['title'] for row in results], ['Distributed Systems'])
        self.assertEqual(results[0]['search_mode'], 'fts')
        self.assertIn('[Distributed]', results[0]['search_preview'])
        self.assertIn('[Tanenbaum]', results[0]['search_preview'])

    def test_full_text_search_accepts_phrase_queries_and_limit(self):
        lib, _ = self.make_library()
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')
        lib.add_book('Distributed Systems Concepts', 'Maarten van Steen')
        lib.add_book('Distributed Algorithms', 'Nancy Lynch')

        results = lib.list_books(query='"distributed systems"', search_mode='fts', limit=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Distributed Systems')
        self.assertEqual(results[0]['search_mode'], 'fts')

    def test_keyword_search_mode_preserves_substring_matching(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('Refactoring', 'Martin Fowler')

        results = lib.list_books(query='robert', search_mode='keyword')

        self.assertEqual([row['title'] for row in results], ['Clean Code'])
        self.assertEqual(results[0]['search_mode'], 'keyword')
        self.assertNotIn('search_preview', results[0])

    def test_overdue_books_only_returns_past_due_loans(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 1))
        lib.checkout(2, 'Sam', loan_days=14, checkout_date=date(2026, 4, 10))

        overdue = lib.overdue_books(date(2026, 4, 15))
        self.assertEqual([row['title'] for row in overdue], ['Clean Code'])

    def test_rejects_invalid_checkout_return_and_search_requests(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.checkout(1, 'Alex')

        with self.assertRaises(LibraryError):
            lib.checkout(1, 'Sam')
        with self.assertRaises(LibraryError):
            lib.return_book(99)
        with self.assertRaises(LibraryError):
            lib.add_book('   ', 'Robert C. Martin')
        with self.assertRaises(LibraryError):
            lib.list_books(query='clean', search_mode='regex')
        with self.assertRaises(LibraryError):
            lib.list_books(query='clean', limit=0)

        lib.fts_enabled = False
        with self.assertRaisesRegex(LibraryError, 'full-text search is not available'):
            lib.list_books(query='clean', search_mode='fts')

    def test_schema_migration_adds_new_columns_and_backfills_search_index(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / 'library.db'
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, available INTEGER DEFAULT 1)')
            conn.execute(
                'INSERT INTO books(id, title, author, available) VALUES (?, ?, ?, ?)',
                (1, 'Database Internals', 'Alex Petrov', 1),
            )

        lib = Library(db)
        with sqlite3.connect(db) as conn:
            columns = {row[1] for row in conn.execute('PRAGMA table_info(books)')}
            fts_count = conn.execute('SELECT COUNT(*) FROM books_fts').fetchone()[0]
        self.assertTrue({'borrower', 'checked_out_at', 'due_date'}.issubset(columns))
        self.assertEqual(fts_count, 1)
        hits = lib.list_books(query='petrov', search_mode='fts')
        self.assertEqual([row['title'] for row in hits], ['Database Internals'])

    def test_cli_search_and_overdue_output(self):
        lib, db = self.make_library()
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 1))

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(['--db', str(db), 'list', '--query', 'distr tanen', '--search-mode', 'fts'])
        output = buffer.getvalue()
        self.assertIn('Distributed Systems', output)
        self.assertIn('match: title=[Distributed]', output)

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(['--db', str(db), 'overdue', '--date', '2026-04-15'])
        overdue_output = buffer.getvalue()
        self.assertIn('checked out to Alex', overdue_output)
        self.assertNotIn('Refactoring', overdue_output)


if __name__ == '__main__':
    unittest.main()
