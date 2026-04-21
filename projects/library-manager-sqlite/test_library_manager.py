import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from library_manager import (
    Library,
    LibraryError,
    build_dashboard_snapshot,
    main,
    render_dashboard_html,
    render_dashboard_markdown,
)


class LibraryTests(unittest.TestCase):
    def make_library(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / 'library.db'
        return Library(db), db

    def test_add_checkout_return_and_persist_loan_history(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')

        due_day = lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 14))
        self.assertEqual(due_day.isoformat(), '2026-04-21')
        checked_out = lib.list_books()[0]
        self.assertFalse(checked_out['available'])
        self.assertEqual(checked_out['borrower'], 'Alex')
        self.assertEqual(checked_out['due_date'], '2026-04-21')

        lib.return_book(1, return_date=date(2026, 4, 20))
        returned = lib.list_books()[0]
        self.assertTrue(returned['available'])
        self.assertIsNone(returned['borrower'])
        self.assertIsNone(returned['due_date'])

        history = lib.loan_history(status='returned', reference_date=date(2026, 4, 21))
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['borrower'], 'Alex')
        self.assertEqual(history[0]['returned_at'], '2026-04-20')
        self.assertEqual(history[0]['loan_status'], 'returned')
        self.assertEqual(history[0]['lateness_days'], 0)

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

    def test_loan_history_filters_active_overdue_and_borrower(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.add_book('Designing Data-Intensive Applications', 'Martin Kleppmann')

        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 1))
        lib.checkout(2, 'Sam', loan_days=14, checkout_date=date(2026, 4, 10))
        lib.checkout(3, 'Alex', loan_days=21, checkout_date=date(2026, 4, 12))
        lib.return_book(3, return_date=date(2026, 4, 20))

        overdue = lib.loan_history(status='overdue', reference_date=date(2026, 4, 15))
        self.assertEqual([row['title'] for row in overdue], ['Clean Code'])
        self.assertEqual(overdue[0]['loan_status'], 'overdue')
        self.assertEqual(overdue[0]['lateness_days'], 7)

        active = lib.loan_history(status='active', reference_date=date(2026, 4, 15))
        self.assertEqual(
            [row['title'] for row in active],
            ['Designing Data-Intensive Applications', 'Refactoring'],
        )

        borrower_history = lib.loan_history(borrower='alex', reference_date=date(2026, 4, 21))
        self.assertEqual([row['title'] for row in borrower_history], ['Designing Data-Intensive Applications', 'Clean Code'])
        self.assertEqual([row['loan_status'] for row in borrower_history], ['returned', 'overdue'])

    def test_circulation_stats_summarize_loans_and_top_borrowers(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.add_book('DDIA', 'Martin Kleppmann')

        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 1))
        lib.return_book(1, return_date=date(2026, 4, 9))
        lib.checkout(2, 'Sam', loan_days=14, checkout_date=date(2026, 4, 10))
        lib.checkout(3, 'Alex', loan_days=21, checkout_date=date(2026, 4, 12))

        stats = lib.circulation_stats(reference_date=date(2026, 4, 26), top_limit=2)

        self.assertEqual(stats['total_books'], 3)
        self.assertEqual(stats['total_borrowers'], 2)
        self.assertEqual(stats['total_loans'], 3)
        self.assertEqual(stats['active_loans'], 2)
        self.assertEqual(stats['overdue_loans'], 1)
        self.assertEqual(stats['completed_loans'], 1)
        self.assertEqual(stats['late_returns'], 1)
        self.assertEqual(stats['average_configured_loan_days'], 14.0)
        self.assertEqual(stats['average_return_days'], 8.0)
        self.assertEqual(stats['top_borrowers'][0]['borrower'], 'Alex')
        self.assertEqual(stats['top_borrowers'][0]['total_loans'], 2)

    def test_rejects_invalid_checkout_return_search_and_history_requests(self):
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
        with self.assertRaises(LibraryError):
            lib.loan_history(status='late')
        with self.assertRaises(LibraryError):
            lib.circulation_stats(top_limit=0)

        lib.fts_enabled = False
        with self.assertRaisesRegex(LibraryError, 'full-text search is not available'):
            lib.list_books(query='clean', search_mode='fts')

    def test_schema_migration_adds_new_columns_backfills_search_index_and_active_loans(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / 'library.db'
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, available INTEGER DEFAULT 1)')
            conn.execute(
                'INSERT INTO books(id, title, author, available) VALUES (?, ?, ?, ?)',
                (1, 'Database Internals', 'Alex Petrov', 1),
            )
            conn.execute('ALTER TABLE books ADD COLUMN borrower TEXT')
            conn.execute('ALTER TABLE books ADD COLUMN checked_out_at TEXT')
            conn.execute('ALTER TABLE books ADD COLUMN due_date TEXT')
            conn.execute(
                'INSERT INTO books(id, title, author, available, borrower, checked_out_at, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (2, 'Designing Data-Intensive Applications', 'Martin Kleppmann', 0, 'Alex', '2026-04-10', '2026-04-24'),
            )

        lib = Library(db)
        with sqlite3.connect(db) as conn:
            columns = {row[1] for row in conn.execute('PRAGMA table_info(books)')}
            fts_count = conn.execute('SELECT COUNT(*) FROM books_fts').fetchone()[0]
            borrower_count = conn.execute('SELECT COUNT(*) FROM borrowers').fetchone()[0]
            active_loan_count = conn.execute('SELECT COUNT(*) FROM loans WHERE returned_at IS NULL').fetchone()[0]
        self.assertTrue({'borrower', 'checked_out_at', 'due_date'}.issubset(columns))
        self.assertEqual(fts_count, 2)
        self.assertEqual(borrower_count, 1)
        self.assertEqual(active_loan_count, 1)
        hits = lib.list_books(query='petrov', search_mode='fts')
        self.assertEqual([row['title'] for row in hits], ['Database Internals'])
        history = lib.loan_history(status='active', reference_date=date(2026, 4, 20))
        self.assertEqual([row['title'] for row in history], ['Designing Data-Intensive Applications'])

    def test_cli_history_and_stats_output(self):
        lib, db = self.make_library()
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 1))
        lib.checkout(2, 'Sam', loan_days=14, checkout_date=date(2026, 4, 10))
        lib.return_book(2, return_date=date(2026, 4, 22))

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(['--db', str(db), 'history', '--status', 'returned', '--borrower', 'sam', '--date', '2026-04-23'])
        history_output = buffer.getvalue()
        self.assertIn('loan #', history_output)
        self.assertIn('Refactoring', history_output)
        self.assertIn('returned 2026-04-22 [returned on time]', history_output)

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(['--db', str(db), 'stats', '--date', '2026-04-23', '--top', '2'])
        stats_output = buffer.getvalue()
        self.assertIn('books: 2', stats_output)
        self.assertIn('borrowers: 2', stats_output)
        self.assertIn('loans: total 2 | active 1 | overdue 1 | returned 1', stats_output)
        self.assertIn('Alex — loans 1', stats_output)

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


    def test_recent_activity_orders_returns_by_return_date(self):
        lib, _ = self.make_library()
        lib.add_book('Clean Code', 'Robert C. Martin')
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')

        lib.checkout(1, 'Alex', loan_days=14, checkout_date=date(2026, 4, 1))
        lib.checkout(2, 'Sam', loan_days=7, checkout_date=date(2026, 4, 20))
        lib.return_book(1, return_date=date(2026, 4, 25))

        activity = lib.recent_activity(reference_date=date(2026, 4, 25), limit=2)

        self.assertEqual(
            [(row['activity_kind'], row['book_id']) for row in activity],
            [('return', 1), ('checkout', 2)],
        )
        self.assertEqual(activity[0]['activity_at'], '2026-04-25')
        self.assertEqual(activity[0]['loan_status'], 'returned')

    def test_dashboard_snapshot_and_renderers_include_portfolio_sections(self):
        lib, _ = self.make_library()
        lib.add_book('Systems | Practice', 'Alice <Bob>')
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')
        lib.add_book('Refactoring', 'Martin Fowler')

        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 10))
        lib.checkout(2, 'Sam', loan_days=21, checkout_date=date(2026, 4, 20))
        lib.checkout(3, 'Alex', loan_days=7, checkout_date=date(2026, 4, 5))
        lib.return_book(3, return_date=date(2026, 4, 24))

        snapshot = build_dashboard_snapshot(
            lib,
            reference_date=date(2026, 4, 25),
            top_limit=3,
            current_limit=5,
            recent_limit=5,
            title='Portfolio dashboard',
            generated_at='2026-04-25T12:00:00Z',
        )

        self.assertEqual(snapshot['summary']['active_loans'], 2)
        self.assertEqual(snapshot['summary']['overdue_loans'], 1)
        self.assertEqual(snapshot['current_total'], 2)
        self.assertEqual(snapshot['recent_activity'][0]['activity_kind'], 'return')
        self.assertEqual(snapshot['generated_at'], '2026-04-25T12:00:00Z')

        markdown = render_dashboard_markdown(snapshot)
        self.assertIn('# Portfolio dashboard', markdown)
        self.assertIn('## Current circulation', markdown)
        self.assertIn('Systems \\| Practice', markdown)
        self.assertIn('2026-04-25T12:00:00Z', markdown)
        self.assertIn('overdue by 8d', markdown)
        self.assertIn('## Top borrowers', markdown)

        html = render_dashboard_html(snapshot)
        self.assertIn('<caption>Books currently checked out at the snapshot date</caption>', html)
        self.assertIn('Portfolio dashboard', html)
        self.assertIn('2026-04-25T12:00:00Z', html)
        self.assertIn('Alice &lt;Bob&gt;', html)
        self.assertIn('status-overdue', html)

    def test_dashboard_snapshot_respects_reference_date_for_future_returns(self):
        lib, _ = self.make_library()
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.checkout(1, 'Alex', loan_days=14, checkout_date=date(2026, 4, 10))
        lib.checkout(2, 'Sam', loan_days=7, checkout_date=date(2026, 4, 26))
        lib.return_book(1, return_date=date(2026, 4, 30))

        snapshot = build_dashboard_snapshot(
            lib,
            reference_date=date(2026, 4, 25),
            recent_limit=5,
            generated_at='2026-04-25T12:00:00Z',
        )

        self.assertEqual(snapshot['summary']['total_loans'], 1)
        self.assertEqual(snapshot['summary']['active_loans'], 1)
        self.assertEqual(snapshot['summary']['completed_loans'], 0)
        self.assertEqual(snapshot['summary']['overdue_loans'], 1)
        self.assertEqual([row['book_id'] for row in snapshot['current_loans']], [1])
        self.assertEqual(snapshot['current_loans'][0]['loan_status'], 'overdue')
        self.assertEqual(
            [(row['activity_kind'], row['book_id']) for row in snapshot['recent_activity']],
            [('checkout', 1)],
        )
        history = lib.loan_history(status='all', reference_date=date(2026, 4, 25))
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['loan_status'], 'overdue')

    def test_cli_dashboard_writes_artifacts_and_supports_stdout_mode(self):
        lib, db = self.make_library()
        lib.add_book('Distributed Systems', 'Andrew S. Tanenbaum')
        lib.add_book('Refactoring', 'Martin Fowler')
        lib.checkout(1, 'Alex', loan_days=7, checkout_date=date(2026, 4, 10))
        lib.checkout(2, 'Sam', loan_days=14, checkout_date=date(2026, 4, 15))
        lib.return_book(2, return_date=date(2026, 4, 20))

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        markdown_path = Path(tmp.name) / 'artifacts' / 'dashboard.md'
        html_path = Path(tmp.name) / 'artifacts' / 'dashboard.html'

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(
                [
                    '--db',
                    str(db),
                    'dashboard',
                    '--date',
                    '2026-04-25',
                    '--markdown-out',
                    str(markdown_path),
                    '--html-out',
                    str(html_path),
                    '--title',
                    'CLI dashboard',
                    '--generated-at',
                    '2026-04-25T12:00:00Z',
                ]
            )
        command_output = buffer.getvalue()
        self.assertIn('dashboard written:', command_output)
        self.assertTrue(markdown_path.exists())
        self.assertTrue(html_path.exists())
        self.assertIn('CLI dashboard', markdown_path.read_text())
        self.assertIn('2026-04-25T12:00:00Z', markdown_path.read_text())
        self.assertIn('Latest checkouts and returns', html_path.read_text())

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(['--db', str(db), 'dashboard', '--date', '2026-04-25'])
        stdout_dashboard = buffer.getvalue()
        self.assertIn('## Recent activity', stdout_dashboard)
        self.assertIn('Distributed Systems', stdout_dashboard)


if __name__ == '__main__':
    unittest.main()
