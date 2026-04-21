import argparse
import csv
import re
import sqlite3
from io import StringIO
from datetime import date, datetime, timezone, timedelta
from html import escape
from pathlib import Path


class LibraryError(Exception):
    pass


BORROWER_TREND_COLORS = ['#2563eb', '#dc2626', '#059669', '#7c3aed', '#d97706', '#0f766e']
GENRE_TREND_COLORS = ['#2563eb', '#059669', '#d97706', '#7c3aed', '#dc2626', '#0f766e']


class Library:
    def __init__(self, db_path='library.db'):
        self.db_path = Path(db_path)
        self.fts_enabled = False
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                'CREATE TABLE IF NOT EXISTS books ('
                'id INTEGER PRIMARY KEY, '
                'title TEXT NOT NULL, '
                'author TEXT NOT NULL, '
                'available INTEGER DEFAULT 1'
                ')'
            )
            columns = {row['name'] for row in conn.execute('PRAGMA table_info(books)')}
            migrations = {
                'genre': 'ALTER TABLE books ADD COLUMN genre TEXT DEFAULT "General"',
                'borrower': 'ALTER TABLE books ADD COLUMN borrower TEXT',
                'checked_out_at': 'ALTER TABLE books ADD COLUMN checked_out_at TEXT',
                'due_date': 'ALTER TABLE books ADD COLUMN due_date TEXT',
            }
            for column, statement in migrations.items():
                if column not in columns:
                    conn.execute(statement)
            conn.execute(
                'UPDATE books SET genre = "General" WHERE genre IS NULL OR trim(genre) = ""'
            )
            self._init_circulation_schema(conn)
            self._backfill_active_loans(conn)
            self.fts_enabled = self._init_search_index(conn)

    def _init_circulation_schema(self, conn):
        conn.execute(
            'CREATE TABLE IF NOT EXISTS borrowers ('
            'id INTEGER PRIMARY KEY, '
            'name TEXT NOT NULL UNIQUE COLLATE NOCASE'
            ')'
        )
        conn.execute(
            'CREATE TABLE IF NOT EXISTS loans ('
            'id INTEGER PRIMARY KEY, '
            'book_id INTEGER NOT NULL, '
            'borrower_id INTEGER NOT NULL, '
            'checked_out_at TEXT NOT NULL, '
            'due_date TEXT NOT NULL, '
            'loan_days INTEGER NOT NULL, '
            'returned_at TEXT, '
            'FOREIGN KEY(book_id) REFERENCES books(id), '
            'FOREIGN KEY(borrower_id) REFERENCES borrowers(id)'
            ')'
        )
        conn.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_loans_one_active_per_book '
            'ON loans(book_id) WHERE returned_at IS NULL'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_loans_borrower_history '
            'ON loans(borrower_id, checked_out_at DESC, id DESC)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_loans_due_active '
            'ON loans(due_date, book_id) WHERE returned_at IS NULL'
        )

    def _init_search_index(self, conn):
        try:
            conn.execute(
                'CREATE VIRTUAL TABLE IF NOT EXISTS books_fts '
                'USING fts5(title, author, book_id UNINDEXED)'
            )
        except sqlite3.OperationalError:
            return False

        book_count = conn.execute('SELECT COUNT(*) AS count FROM books').fetchone()['count']
        indexed_count = conn.execute('SELECT COUNT(*) AS count FROM books_fts').fetchone()['count']
        if indexed_count != book_count:
            conn.execute('DELETE FROM books_fts')
            conn.execute(
                'INSERT INTO books_fts(rowid, title, author, book_id) '
                'SELECT id, title, author, id FROM books ORDER BY id'
            )
        return True

    @staticmethod
    def _normalize_fts_query(query):
        query = query.strip()
        if not query:
            return ''
        if re.search(r'[*():"]|\b(?:AND|OR|NOT|NEAR)\b', query):
            return query
        tokens = re.findall(r'[\w]+', query.lower(), flags=re.UNICODE)
        return ' AND '.join(f'{token}*' for token in tokens)

    @staticmethod
    def _parse_iso_date(value):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _ensure_borrower(self, conn, borrower_name):
        borrower_name = borrower_name.strip()
        if not borrower_name:
            raise LibraryError('borrower is required')
        try:
            cursor = conn.execute('INSERT INTO borrowers(name) VALUES (?)', (borrower_name,))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            row = conn.execute(
                'SELECT id FROM borrowers WHERE name = ? COLLATE NOCASE',
                (borrower_name,),
            ).fetchone()
            if not row:
                raise
            return row['id']

    @staticmethod
    def _normalize_genre(genre):
        normalized = (genre or 'General').strip()
        if not normalized:
            raise LibraryError('genre is required when provided')
        return normalized

    def _backfill_active_loans(self, conn):
        legacy_rows = conn.execute(
            'SELECT id, borrower, checked_out_at, due_date '
            'FROM books '
            'WHERE available = 0 '
            'AND borrower IS NOT NULL '
            'AND checked_out_at IS NOT NULL '
            'AND due_date IS NOT NULL'
        ).fetchall()
        for row in legacy_rows:
            existing = conn.execute(
                'SELECT id FROM loans WHERE book_id = ? AND returned_at IS NULL',
                (row['id'],),
            ).fetchone()
            if existing:
                continue
            borrower_id = self._ensure_borrower(conn, row['borrower'])
            checked_out_day = self._parse_iso_date(row['checked_out_at'])
            due_day = self._parse_iso_date(row['due_date'])
            loan_days = 14
            if checked_out_day and due_day:
                loan_days = max((due_day - checked_out_day).days, 1)
            conn.execute(
                'INSERT INTO loans(book_id, borrower_id, checked_out_at, due_date, loan_days, returned_at) '
                'VALUES (?, ?, ?, ?, ?, NULL)',
                (row['id'], borrower_id, row['checked_out_at'], row['due_date'], loan_days),
            )

    def add_book(self, title, author, genre='General'):
        title = title.strip()
        author = author.strip()
        genre = self._normalize_genre(genre)
        if not title or not author:
            raise LibraryError('title and author are required')
        with self._connect() as conn:
            cursor = conn.execute(
                'INSERT INTO books(title, author, genre, available, borrower, checked_out_at, due_date) '
                'VALUES (?, ?, ?, 1, NULL, NULL, NULL)',
                (title, author, genre),
            )
            if self.fts_enabled:
                book_id = cursor.lastrowid
                conn.execute(
                    'INSERT INTO books_fts(rowid, title, author, book_id) VALUES (?, ?, ?, ?)',
                    (book_id, title, author, book_id),
                )

    def checkout(self, book_id, borrower, loan_days=14, checkout_date=None):
        borrower = borrower.strip()
        if not borrower:
            raise LibraryError('borrower is required')
        if loan_days <= 0:
            raise LibraryError('loan_days must be positive')

        checkout_day = checkout_date or date.today()
        due_day = checkout_day + timedelta(days=loan_days)

        with self._connect() as conn:
            book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
            if not book:
                raise LibraryError(f'book #{book_id} not found')
            if not book['available']:
                raise LibraryError(f'book #{book_id} is already checked out')
            borrower_id = self._ensure_borrower(conn, borrower)
            conn.execute(
                'UPDATE books SET available = 0, borrower = ?, checked_out_at = ?, due_date = ? WHERE id = ?',
                (borrower, checkout_day.isoformat(), due_day.isoformat(), book_id),
            )
            conn.execute(
                'INSERT INTO loans(book_id, borrower_id, checked_out_at, due_date, loan_days, returned_at) '
                'VALUES (?, ?, ?, ?, ?, NULL)',
                (book_id, borrower_id, checkout_day.isoformat(), due_day.isoformat(), loan_days),
            )
            return due_day

    def _reconstruct_active_loan(self, conn, book):
        if not book['borrower'] or not book['checked_out_at'] or not book['due_date']:
            raise LibraryError(f'book #{book["id"]} has no active loan record')
        borrower_id = self._ensure_borrower(conn, book['borrower'])
        checked_out_day = self._parse_iso_date(book['checked_out_at'])
        due_day = self._parse_iso_date(book['due_date'])
        loan_days = 14
        if checked_out_day and due_day:
            loan_days = max((due_day - checked_out_day).days, 1)
        cursor = conn.execute(
            'INSERT INTO loans(book_id, borrower_id, checked_out_at, due_date, loan_days, returned_at) '
            'VALUES (?, ?, ?, ?, ?, NULL)',
            (book['id'], borrower_id, book['checked_out_at'], book['due_date'], loan_days),
        )
        return cursor.lastrowid

    def return_book(self, book_id, return_date=None):
        return_day = return_date or date.today()
        with self._connect() as conn:
            book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
            if not book:
                raise LibraryError(f'book #{book_id} not found')
            if book['available']:
                raise LibraryError(f'book #{book_id} is not checked out')
            active_loan = conn.execute(
                'SELECT id FROM loans WHERE book_id = ? AND returned_at IS NULL ORDER BY id DESC LIMIT 1',
                (book_id,),
            ).fetchone()
            loan_id = active_loan['id'] if active_loan else self._reconstruct_active_loan(conn, book)
            conn.execute(
                'UPDATE loans SET returned_at = ? WHERE id = ? AND returned_at IS NULL',
                (return_day.isoformat(), loan_id),
            )
            conn.execute(
                'UPDATE books SET available = 1, borrower = NULL, checked_out_at = NULL, due_date = NULL WHERE id = ?',
                (book_id,),
            )

    def _list_books_keyword(self, query=None, limit=None):
        sql = 'SELECT * FROM books'
        params = []
        if query:
            sql += ' WHERE lower(title) LIKE ? OR lower(author) LIKE ?'
            like = f'%{query.lower()}%'
            params.extend([like, like])
        sql += ' ORDER BY id'
        if limit is not None:
            sql += ' LIMIT ?'
            params.append(limit)
        with self._connect() as conn:
            rows = [dict(r) for r in conn.execute(sql, params)]
        if query:
            for row in rows:
                row['search_mode'] = 'keyword'
        return rows

    def _list_books_fts(self, query, limit=None):
        if not self.fts_enabled:
            raise LibraryError('full-text search is not available in this SQLite build')

        normalized_query = self._normalize_fts_query(query)
        if not normalized_query:
            return []

        sql = (
            'SELECT b.*, '
            'bm25(books_fts, 5.0, 3.0) AS score, '
            "highlight(books_fts, 0, '[', ']') AS title_highlight, "
            "highlight(books_fts, 1, '[', ']') AS author_highlight "
            'FROM books_fts '
            'JOIN books AS b ON b.id = books_fts.book_id '
            'WHERE books_fts MATCH ? '
            'ORDER BY score, b.id'
        )
        params = [normalized_query]
        if limit is not None:
            sql += ' LIMIT ?'
            params.append(limit)

        with self._connect() as conn:
            rows = []
            for result in conn.execute(sql, params):
                row = dict(result)
                row['search_mode'] = 'fts'
                row['search_score'] = row.pop('score')
                title_highlight = row.pop('title_highlight', None)
                author_highlight = row.pop('author_highlight', None)
                preview_parts = []
                if title_highlight and title_highlight != row['title']:
                    preview_parts.append(f'title={title_highlight}')
                if author_highlight and author_highlight != row['author']:
                    preview_parts.append(f'author={author_highlight}')
                row['search_preview'] = '; '.join(preview_parts) or None
                rows.append(row)
            return rows

    def list_books(self, query=None, search_mode='auto', limit=None):
        if search_mode not in {'auto', 'keyword', 'fts'}:
            raise LibraryError('search_mode must be one of auto, keyword, or fts')
        if limit is not None and limit <= 0:
            raise LibraryError('limit must be positive when provided')

        query = query.strip() if query else None
        if query and search_mode in {'auto', 'fts'}:
            try:
                return self._list_books_fts(query=query, limit=limit)
            except LibraryError:
                if search_mode == 'fts':
                    raise
            except sqlite3.OperationalError as exc:
                if search_mode == 'fts':
                    raise LibraryError(f'invalid full-text query: {query}') from exc
        return self._list_books_keyword(query=query, limit=limit)

    def overdue_books(self, reference_date=None):
        ref = (reference_date or date.today()).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT * FROM books WHERE available = 0 AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date, id',
                (ref,),
            )
            return [dict(r) for r in rows]

    def loan_history(self, book_id=None, borrower=None, status='all', limit=None, reference_date=None):
        if status not in {'all', 'active', 'overdue', 'returned'}:
            raise LibraryError('status must be one of all, active, overdue, or returned')
        if limit is not None and limit <= 0:
            raise LibraryError('limit must be positive when provided')

        reference_iso = (reference_date or date.today()).isoformat()
        sql = (
            'SELECT '
            'l.id AS loan_id, '
            'b.id AS book_id, '
            'b.title, '
            'b.author, '
            'br.name AS borrower, '
            'l.checked_out_at, '
            'l.due_date, '
            'l.returned_at, '
            'l.loan_days, '
            'CASE '
            'WHEN l.returned_at IS NOT NULL AND l.returned_at <= ? THEN "returned" '
            'WHEN l.due_date < ? THEN "overdue" '
            'ELSE "active" '
            'END AS loan_status, '
            'CASE '
            'WHEN l.returned_at IS NOT NULL AND l.returned_at <= ? AND l.returned_at > l.due_date '
            'THEN CAST(julianday(l.returned_at) - julianday(l.due_date) AS INTEGER) '
            'WHEN (l.returned_at IS NULL OR l.returned_at > ?) AND l.due_date < ? '
            'THEN CAST(julianday(?) - julianday(l.due_date) AS INTEGER) '
            'ELSE 0 '
            'END AS lateness_days '
            'FROM loans AS l '
            'JOIN books AS b ON b.id = l.book_id '
            'JOIN borrowers AS br ON br.id = l.borrower_id '
            'WHERE l.checked_out_at <= ?'
        )
        params = [reference_iso, reference_iso, reference_iso, reference_iso, reference_iso, reference_iso, reference_iso]

        if book_id is not None:
            sql += ' AND b.id = ?'
            params.append(book_id)
        if borrower:
            sql += ' AND lower(br.name) LIKE ?'
            params.append(f'%{borrower.lower()}%')
        if status == 'active':
            sql += ' AND (l.returned_at IS NULL OR l.returned_at > ?) AND l.due_date >= ?'
            params.extend([reference_iso, reference_iso])
        elif status == 'overdue':
            sql += ' AND (l.returned_at IS NULL OR l.returned_at > ?) AND l.due_date < ?'
            params.extend([reference_iso, reference_iso])
        elif status == 'returned':
            sql += ' AND l.returned_at IS NOT NULL AND l.returned_at <= ?'
            params.append(reference_iso)

        sql += ' ORDER BY l.checked_out_at DESC, l.id DESC'
        if limit is not None:
            sql += ' LIMIT ?'
            params.append(limit)

        with self._connect() as conn:
            return [dict(r) for r in conn.execute(sql, params)]

    def circulation_stats(self, reference_date=None, top_limit=5):
        if top_limit <= 0:
            raise LibraryError('top_limit must be positive')

        reference_iso = (reference_date or date.today()).isoformat()
        with self._connect() as conn:
            summary = dict(
                conn.execute(
                    'SELECT '
                    '(SELECT COUNT(*) FROM books) AS total_books, '
                    '(SELECT COUNT(*) FROM borrowers) AS total_borrowers, '
                    'COUNT(*) AS total_loans, '
                    'COALESCE(SUM(CASE WHEN returned_at IS NULL OR returned_at > ? THEN 1 ELSE 0 END), 0) AS active_loans, '
                    'COALESCE(SUM(CASE WHEN (returned_at IS NULL OR returned_at > ?) AND due_date < ? THEN 1 ELSE 0 END), 0) AS overdue_loans, '
                    'COALESCE(SUM(CASE WHEN returned_at IS NOT NULL AND returned_at <= ? THEN 1 ELSE 0 END), 0) AS completed_loans, '
                    'ROUND(AVG(CAST(loan_days AS REAL)), 2) AS average_configured_loan_days, '
                    'ROUND(AVG(CASE WHEN returned_at IS NOT NULL AND returned_at <= ? THEN julianday(returned_at) - julianday(checked_out_at) END), 2) AS average_return_days, '
                    'COALESCE(SUM(CASE WHEN returned_at IS NOT NULL AND returned_at <= ? AND returned_at > due_date THEN 1 ELSE 0 END), 0) AS late_returns '
                    'FROM loans '
                    'WHERE checked_out_at <= ?',
                    (
                        reference_iso,
                        reference_iso,
                        reference_iso,
                        reference_iso,
                        reference_iso,
                        reference_iso,
                        reference_iso,
                    ),
                ).fetchone()
            )
            top_borrowers = [
                dict(r)
                for r in conn.execute(
                    'SELECT '
                    'br.name AS borrower, '
                    'COUNT(*) AS total_loans, '
                    'SUM(CASE WHEN l.returned_at IS NULL OR l.returned_at > ? THEN 1 ELSE 0 END) AS active_loans, '
                    'SUM(CASE WHEN (l.returned_at IS NULL OR l.returned_at > ?) AND l.due_date < ? THEN 1 ELSE 0 END) AS overdue_loans, '
                    'MAX(l.checked_out_at) AS last_checkout_at '
                    'FROM loans AS l '
                    'JOIN borrowers AS br ON br.id = l.borrower_id '
                    'WHERE l.checked_out_at <= ? '
                    'GROUP BY br.id, br.name '
                    'ORDER BY total_loans DESC, active_loans DESC, br.name COLLATE NOCASE '
                    'LIMIT ?',
                    (reference_iso, reference_iso, reference_iso, reference_iso, top_limit),
                )
            ]
        summary['top_borrowers'] = top_borrowers
        return summary

    def current_circulation(self, reference_date=None, limit=None):
        if limit is not None and limit <= 0:
            raise LibraryError('limit must be positive when provided')

        reference_iso = (reference_date or date.today()).isoformat()
        sql = (
            'SELECT '
            'l.id AS loan_id, '
            'b.id AS book_id, '
            'b.title, '
            'b.author, '
            'br.name AS borrower, '
            'l.checked_out_at, '
            'l.due_date, '
            'l.returned_at, '
            'l.loan_days, '
            'CASE WHEN l.due_date < ? THEN "overdue" ELSE "active" END AS loan_status, '
            'CASE '
            'WHEN l.due_date < ? THEN CAST(julianday(?) - julianday(l.due_date) AS INTEGER) '
            'ELSE 0 '
            'END AS lateness_days '
            'FROM loans AS l '
            'JOIN books AS b ON b.id = l.book_id '
            'JOIN borrowers AS br ON br.id = l.borrower_id '
            'WHERE l.checked_out_at <= ? AND (l.returned_at IS NULL OR l.returned_at > ?) '
            'ORDER BY l.due_date, l.checked_out_at DESC, l.id DESC'
        )
        params = [reference_iso, reference_iso, reference_iso, reference_iso, reference_iso]
        if limit is not None:
            sql += ' LIMIT ?'
            params.append(limit)

        with self._connect() as conn:
            return [dict(r) for r in conn.execute(sql, params)]

    def recent_activity(self, reference_date=None, limit=5):
        if limit <= 0:
            raise LibraryError('limit must be positive')

        reference_iso = (reference_date or date.today()).isoformat()
        sql = (
            'SELECT '
            'l.id AS loan_id, '
            'b.id AS book_id, '
            'b.title, '
            'b.author, '
            'br.name AS borrower, '
            'l.checked_out_at, '
            'l.due_date, '
            'l.returned_at, '
            'l.loan_days, '
            'CASE '
            'WHEN l.returned_at IS NOT NULL AND l.returned_at <= ? THEN "returned" '
            'WHEN l.due_date < ? THEN "overdue" '
            'ELSE "active" '
            'END AS loan_status, '
            'CASE '
            'WHEN l.returned_at IS NOT NULL AND l.returned_at <= ? AND l.returned_at > l.due_date '
            'THEN CAST(julianday(l.returned_at) - julianday(l.due_date) AS INTEGER) '
            'WHEN (l.returned_at IS NULL OR l.returned_at > ?) AND l.due_date < ? '
            'THEN CAST(julianday(?) - julianday(l.due_date) AS INTEGER) '
            'ELSE 0 '
            'END AS lateness_days, '
            'CASE WHEN l.returned_at IS NOT NULL AND l.returned_at <= ? THEN l.returned_at ELSE l.checked_out_at END AS activity_at, '
            'CASE WHEN l.returned_at IS NOT NULL AND l.returned_at <= ? THEN "return" ELSE "checkout" END AS activity_kind '
            'FROM loans AS l '
            'JOIN books AS b ON b.id = l.book_id '
            'JOIN borrowers AS br ON br.id = l.borrower_id '
            'WHERE l.checked_out_at <= ? '
            'ORDER BY activity_at DESC, l.id DESC '
            'LIMIT ?'
        )
        params = [
            reference_iso,
            reference_iso,
            reference_iso,
            reference_iso,
            reference_iso,
            reference_iso,
            reference_iso,
            reference_iso,
            reference_iso,
            limit,
        ]

        with self._connect() as conn:
            return [dict(r) for r in conn.execute(sql, params)]

    def circulation_trends(self, start_date=None, end_date=None):
        today = date.today()
        with self._connect() as conn:
            rows = [
                dict(r)
                for r in conn.execute(
                    'SELECT checked_out_at, due_date, returned_at FROM loans ORDER BY checked_out_at, id'
                )
            ]

        parsed_loans = []
        min_checkout_day = None
        max_activity_day = None
        for row in rows:
            checked_out_day = self._parse_iso_date(row['checked_out_at'])
            due_day = self._parse_iso_date(row['due_date'])
            returned_day = self._parse_iso_date(row['returned_at'])
            if checked_out_day is None or due_day is None:
                continue
            parsed_loans.append(
                {
                    'checked_out_day': checked_out_day,
                    'due_day': due_day,
                    'returned_day': returned_day,
                }
            )
            min_checkout_day = checked_out_day if min_checkout_day is None else min(min_checkout_day, checked_out_day)
            activity_day = returned_day or checked_out_day
            max_activity_day = activity_day if max_activity_day is None else max(max_activity_day, activity_day)

        resolved_start = start_date or min_checkout_day or today
        resolved_end = end_date or max(max_activity_day or resolved_start, today)
        if resolved_end < resolved_start:
            raise LibraryError('end date must be on or after start date')

        points = []
        current_day = resolved_start
        while current_day <= resolved_end:
            active_loans = 0
            overdue_loans = 0
            completed_loans = 0
            late_returns = 0
            checkouts_started = 0
            returns_completed = 0

            for loan in parsed_loans:
                if loan['checked_out_day'] == current_day:
                    checkouts_started += 1
                if loan['returned_day'] == current_day:
                    returns_completed += 1
                if loan['checked_out_day'] <= current_day and (
                    loan['returned_day'] is None or loan['returned_day'] > current_day
                ):
                    active_loans += 1
                    if loan['due_day'] < current_day:
                        overdue_loans += 1
                if loan['returned_day'] is not None and loan['returned_day'] <= current_day:
                    completed_loans += 1
                    if loan['returned_day'] > loan['due_day']:
                        late_returns += 1

            points.append(
                {
                    'date': current_day.isoformat(),
                    'active_loans': active_loans,
                    'overdue_loans': overdue_loans,
                    'completed_loans': completed_loans,
                    'late_returns': late_returns,
                    'checkouts_started': checkouts_started,
                    'returns_completed': returns_completed,
                }
            )
            current_day += timedelta(days=1)
        return points

    def borrower_trend_breakdown(self, start_date=None, end_date=None, top_limit=4):
        if top_limit <= 0:
            raise LibraryError('top_limit must be positive')

        today = date.today()
        with self._connect() as conn:
            rows = [
                dict(r)
                for r in conn.execute(
                    'SELECT '
                    'br.name AS borrower, '
                    'l.checked_out_at, '
                    'l.due_date, '
                    'l.returned_at '
                    'FROM loans AS l '
                    'JOIN borrowers AS br ON br.id = l.borrower_id '
                    'ORDER BY l.checked_out_at, l.id'
                )
            ]

        parsed_loans = []
        min_checkout_day = None
        max_activity_day = None
        for row in rows:
            checked_out_day = self._parse_iso_date(row['checked_out_at'])
            due_day = self._parse_iso_date(row['due_date'])
            returned_day = self._parse_iso_date(row['returned_at'])
            if checked_out_day is None or due_day is None:
                continue
            parsed_loans.append(
                {
                    'borrower': row['borrower'],
                    'checked_out_day': checked_out_day,
                    'due_day': due_day,
                    'returned_day': returned_day,
                }
            )
            min_checkout_day = checked_out_day if min_checkout_day is None else min(min_checkout_day, checked_out_day)
            activity_day = returned_day or checked_out_day
            max_activity_day = activity_day if max_activity_day is None else max(max_activity_day, activity_day)

        resolved_start = start_date or min_checkout_day or today
        resolved_end = end_date or max(max_activity_day or resolved_start, today)
        if resolved_end < resolved_start:
            raise LibraryError('end date must be on or after start date')

        borrower_candidates = {}
        for loan in parsed_loans:
            if loan['checked_out_day'] > resolved_end:
                continue
            if loan['returned_day'] is not None and loan['returned_day'] < resolved_start:
                continue
            borrower = loan['borrower']
            summary = borrower_candidates.setdefault(
                borrower,
                {
                    'borrower': borrower,
                    'total_loans': 0,
                    'last_checkout_ordinal': 0,
                    'last_checkout_at': None,
                },
            )
            summary['total_loans'] += 1
            summary['last_checkout_ordinal'] = max(
                summary['last_checkout_ordinal'],
                loan['checked_out_day'].toordinal(),
            )
            checkout_iso = loan['checked_out_day'].isoformat()
            if summary['last_checkout_at'] is None or checkout_iso > summary['last_checkout_at']:
                summary['last_checkout_at'] = checkout_iso

        selected_borrowers = sorted(
            borrower_candidates.values(),
            key=lambda row: (-row['total_loans'], -row['last_checkout_ordinal'], row['borrower'].lower()),
        )[:top_limit]
        selected_names = [row['borrower'] for row in selected_borrowers]

        borrower_summaries = {
            row['borrower']: {
                'borrower': row['borrower'],
                'total_loans': row['total_loans'],
                'last_checkout_at': row['last_checkout_at'],
                'peak_active_loans': 0,
                'peak_overdue_loans': 0,
                'total_checkouts_started': 0,
                'total_returns_completed': 0,
                'days_with_active_loans': 0,
            }
            for row in selected_borrowers
        }

        points = []
        current_day = resolved_start
        while current_day <= resolved_end:
            borrower_points = []
            for borrower in selected_names:
                active_loans = 0
                overdue_loans = 0
                checkouts_started = 0
                returns_completed = 0

                for loan in parsed_loans:
                    if loan['borrower'] != borrower:
                        continue
                    if loan['checked_out_day'] == current_day:
                        checkouts_started += 1
                    if loan['returned_day'] == current_day:
                        returns_completed += 1
                    if loan['checked_out_day'] <= current_day and (
                        loan['returned_day'] is None or loan['returned_day'] > current_day
                    ):
                        active_loans += 1
                        if loan['due_day'] < current_day:
                            overdue_loans += 1

                borrower_summaries[borrower]['peak_active_loans'] = max(
                    borrower_summaries[borrower]['peak_active_loans'],
                    active_loans,
                )
                borrower_summaries[borrower]['peak_overdue_loans'] = max(
                    borrower_summaries[borrower]['peak_overdue_loans'],
                    overdue_loans,
                )
                borrower_summaries[borrower]['total_checkouts_started'] += checkouts_started
                borrower_summaries[borrower]['total_returns_completed'] += returns_completed
                if active_loans:
                    borrower_summaries[borrower]['days_with_active_loans'] += 1

                borrower_points.append(
                    {
                        'borrower': borrower,
                        'active_loans': active_loans,
                        'overdue_loans': overdue_loans,
                        'checkouts_started': checkouts_started,
                        'returns_completed': returns_completed,
                    }
                )

            points.append({'date': current_day.isoformat(), 'borrowers': borrower_points})
            current_day += timedelta(days=1)

        return {
            'start_date': resolved_start.isoformat(),
            'end_date': resolved_end.isoformat(),
            'borrowers': selected_names,
            'points': points,
            'summary': [borrower_summaries[name] for name in selected_names],
        }

    def genre_trend_breakdown(self, start_date=None, end_date=None, top_limit=4):
        if top_limit <= 0:
            raise LibraryError('top_limit must be positive')

        today = date.today()
        with self._connect() as conn:
            rows = [
                dict(r)
                for r in conn.execute(
                    'SELECT '
                    'COALESCE(NULLIF(trim(b.genre), ""), "General") AS genre, '
                    'l.checked_out_at, '
                    'l.due_date, '
                    'l.returned_at '
                    'FROM loans AS l '
                    'JOIN books AS b ON b.id = l.book_id '
                    'ORDER BY l.checked_out_at, l.id'
                )
            ]

        parsed_loans = []
        min_checkout_day = None
        max_activity_day = None
        for row in rows:
            checked_out_day = self._parse_iso_date(row['checked_out_at'])
            due_day = self._parse_iso_date(row['due_date'])
            returned_day = self._parse_iso_date(row['returned_at'])
            if checked_out_day is None or due_day is None:
                continue
            parsed_loans.append(
                {
                    'genre': row['genre'],
                    'checked_out_day': checked_out_day,
                    'due_day': due_day,
                    'returned_day': returned_day,
                }
            )
            min_checkout_day = checked_out_day if min_checkout_day is None else min(min_checkout_day, checked_out_day)
            activity_day = returned_day or checked_out_day
            max_activity_day = activity_day if max_activity_day is None else max(max_activity_day, activity_day)

        resolved_start = start_date or min_checkout_day or today
        resolved_end = end_date or max(max_activity_day or resolved_start, today)
        if resolved_end < resolved_start:
            raise LibraryError('end date must be on or after start date')

        genre_candidates = {}
        for loan in parsed_loans:
            if loan['checked_out_day'] > resolved_end:
                continue
            if loan['returned_day'] is not None and loan['returned_day'] < resolved_start:
                continue
            genre = loan['genre']
            summary = genre_candidates.setdefault(
                genre,
                {
                    'genre': genre,
                    'total_loans': 0,
                    'last_checkout_ordinal': 0,
                    'last_checkout_at': None,
                },
            )
            summary['total_loans'] += 1
            summary['last_checkout_ordinal'] = max(
                summary['last_checkout_ordinal'],
                loan['checked_out_day'].toordinal(),
            )
            checkout_iso = loan['checked_out_day'].isoformat()
            if summary['last_checkout_at'] is None or checkout_iso > summary['last_checkout_at']:
                summary['last_checkout_at'] = checkout_iso

        selected_genres = sorted(
            genre_candidates.values(),
            key=lambda row: (-row['total_loans'], -row['last_checkout_ordinal'], row['genre'].lower()),
        )[:top_limit]
        selected_names = [row['genre'] for row in selected_genres]

        genre_summaries = {
            row['genre']: {
                'genre': row['genre'],
                'total_loans': row['total_loans'],
                'last_checkout_at': row['last_checkout_at'],
                'peak_active_loans': 0,
                'peak_overdue_loans': 0,
                'total_checkouts_started': 0,
                'total_returns_completed': 0,
                'days_with_active_loans': 0,
            }
            for row in selected_genres
        }

        points = []
        current_day = resolved_start
        while current_day <= resolved_end:
            genre_points = []
            for genre in selected_names:
                active_loans = 0
                overdue_loans = 0
                checkouts_started = 0
                returns_completed = 0

                for loan in parsed_loans:
                    if loan['genre'] != genre:
                        continue
                    if loan['checked_out_day'] == current_day:
                        checkouts_started += 1
                    if loan['returned_day'] == current_day:
                        returns_completed += 1
                    if loan['checked_out_day'] <= current_day and (
                        loan['returned_day'] is None or loan['returned_day'] > current_day
                    ):
                        active_loans += 1
                        if loan['due_day'] < current_day:
                            overdue_loans += 1

                genre_summaries[genre]['peak_active_loans'] = max(
                    genre_summaries[genre]['peak_active_loans'],
                    active_loans,
                )
                genre_summaries[genre]['peak_overdue_loans'] = max(
                    genre_summaries[genre]['peak_overdue_loans'],
                    overdue_loans,
                )
                genre_summaries[genre]['total_checkouts_started'] += checkouts_started
                genre_summaries[genre]['total_returns_completed'] += returns_completed
                if active_loans:
                    genre_summaries[genre]['days_with_active_loans'] += 1

                genre_points.append(
                    {
                        'genre': genre,
                        'active_loans': active_loans,
                        'overdue_loans': overdue_loans,
                        'checkouts_started': checkouts_started,
                        'returns_completed': returns_completed,
                    }
                )

            points.append({'date': current_day.isoformat(), 'genres': genre_points})
            current_day += timedelta(days=1)

        return {
            'start_date': resolved_start.isoformat(),
            'end_date': resolved_end.isoformat(),
            'genres': selected_names,
            'points': points,
            'summary': [genre_summaries[name] for name in selected_names],
        }



def format_book(row):
    state = 'available' if row['available'] else f"checked out to {row['borrower']} (due {row['due_date']})"
    genre = row.get('genre') or 'General'
    rendered = f"#{row['id']} {row['title']} - {row['author']} [genre: {genre}] [{state}]"
    preview = row.get('search_preview')
    if preview:
        rendered += f"\n    match: {preview}"
    return rendered



def describe_loan_status(row):
    if row['loan_status'] == 'returned':
        if row['lateness_days'] > 0:
            return f"returned late by {row['lateness_days']}d"
        return 'returned on time'
    if row['loan_status'] == 'overdue':
        return f"overdue by {row['lateness_days']}d"
    return 'active'



def format_loan(row):
    returned_at = row['returned_at'] or '-'
    return (
        f"loan #{row['loan_id']} | book #{row['book_id']} {row['title']} - {row['author']} | "
        f"borrower: {row['borrower']} | out {row['checked_out_at']} | due {row['due_date']} | "
        f"returned {returned_at} [{describe_loan_status(row)}]"
    )



def _format_days_metric(value):
    return 'n/a' if value is None else f'{value}d'


def _format_percent(value):
    percentage = value * 100
    rounded = round(percentage)
    if abs(percentage - rounded) < 0.05:
        return f'{rounded}%'
    return f'{percentage:.1f}%'


def _heatmap_fill(value, max_value):
    ratio = value / max(max_value, 1)
    if ratio <= 0:
        return '#f8fafc'
    if ratio <= 0.2:
        return '#dbeafe'
    if ratio <= 0.4:
        return '#93c5fd'
    if ratio <= 0.6:
        return '#60a5fa'
    if ratio <= 0.8:
        return '#2563eb'
    return '#1d4ed8'


def _heatmap_text_fill(value, max_value):
    ratio = value / max(max_value, 1)
    return '#ffffff' if ratio >= 0.55 else '#0f172a'



def format_stats(stats):
    lines = [
        f"books: {stats['total_books']}",
        f"borrowers: {stats['total_borrowers']}",
        (
            'loans: '
            f"total {stats['total_loans']} | active {stats['active_loans']} | "
            f"overdue {stats['overdue_loans']} | returned {stats['completed_loans']}"
        ),
        (
            'averages: '
            f"configured loan {_format_days_metric(stats['average_configured_loan_days'])} | "
            f"actual return {_format_days_metric(stats['average_return_days'])}"
        ),
        f"late returns: {stats['late_returns']}",
    ]
    if stats['top_borrowers']:
        lines.append('top borrowers:')
        for row in stats['top_borrowers']:
            lines.append(
                '  '
                f"{row['borrower']} — loans {row['total_loans']}, "
                f"active {row['active_loans']}, overdue {row['overdue_loans']}, "
                f"last checkout {row['last_checkout_at']}"
            )
    else:
        lines.append('top borrowers: none yet')
    return '\n'.join(lines)



def _utc_timestamp_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')



def _markdown_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')



def _render_markdown_table(headers, rows):
    table = [
        '| ' + ' | '.join(headers) + ' |',
        '| ' + ' | '.join('---' for _ in headers) + ' |',
    ]
    for row in rows:
        table.append('| ' + ' | '.join(_markdown_cell(cell) for cell in row) + ' |')
    return '\n'.join(table)



def _write_text_output(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')



def build_dashboard_snapshot(
    library,
    reference_date=None,
    top_limit=5,
    current_limit=8,
    recent_limit=8,
    title='Library circulation dashboard',
    generated_at=None,
):
    if current_limit <= 0:
        raise LibraryError('current_limit must be positive')
    if recent_limit <= 0:
        raise LibraryError('recent_limit must be positive')

    reference_day = reference_date or date.today()
    summary = library.circulation_stats(reference_date=reference_day, top_limit=top_limit)
    current_loans = library.current_circulation(reference_date=reference_day, limit=current_limit)
    recent_activity = library.recent_activity(reference_date=reference_day, limit=recent_limit)
    return {
        'title': title.strip() or 'Library circulation dashboard',
        'reference_date': reference_day.isoformat(),
        'generated_at': generated_at or _utc_timestamp_iso(),
        'summary': summary,
        'current_loans': current_loans,
        'current_total': summary['active_loans'],
        'recent_activity': recent_activity,
        'limits': {
            'top_borrowers': top_limit,
            'current_loans': current_limit,
            'recent_activity': recent_limit,
        },
    }



def render_dashboard_markdown(snapshot):
    summary = snapshot['summary']
    lines = [
        f"# {snapshot['title']}",
        '',
        f"- Snapshot date: {snapshot['reference_date']}",
        f"- Generated at: {snapshot['generated_at']}",
        '',
        '## Summary',
        '',
        f"- Books: {summary['total_books']}",
        f"- Borrowers: {summary['total_borrowers']}",
        f"- Current loans: {summary['active_loans']}",
        f"- Overdue loans: {summary['overdue_loans']}",
        f"- Returned loans: {summary['completed_loans']}",
        f"- Late returns: {summary['late_returns']}",
        f"- Average configured loan: {_format_days_metric(summary['average_configured_loan_days'])}",
        f"- Average actual return: {_format_days_metric(summary['average_return_days'])}",
    ]
    if summary['overdue_loans']:
        lines.append(f"- Attention: {summary['overdue_loans']} overdue loan(s) need follow-up.")

    lines.extend(['', '## Current circulation', ''])
    if snapshot['current_loans']:
        if len(snapshot['current_loans']) < snapshot['current_total']:
            lines.append(
                f"Showing {len(snapshot['current_loans'])} of {snapshot['current_total']} currently checked-out books."
            )
            lines.append('')
        lines.append(
            _render_markdown_table(
                ['Status', 'Book', 'Borrower', 'Checked out', 'Due', 'Loan days'],
                [
                    [
                        describe_loan_status(row),
                        f"#{row['book_id']} {row['title']} — {row['author']}",
                        row['borrower'],
                        row['checked_out_at'],
                        row['due_date'],
                        row['loan_days'],
                    ]
                    for row in snapshot['current_loans']
                ],
            )
        )
    else:
        lines.append('_No books are currently checked out._')

    lines.extend(['', '## Recent activity', ''])
    if snapshot['recent_activity']:
        lines.append(
            _render_markdown_table(
                ['Date', 'Event', 'Book', 'Borrower', 'Outcome'],
                [
                    [
                        row['activity_at'],
                        row['activity_kind'],
                        f"#{row['book_id']} {row['title']} — {row['author']}",
                        row['borrower'],
                        describe_loan_status(row),
                    ]
                    for row in snapshot['recent_activity']
                ],
            )
        )
    else:
        lines.append('_No loan activity yet._')

    lines.extend(['', '## Top borrowers', ''])
    if summary['top_borrowers']:
        lines.append(
            _render_markdown_table(
                ['Borrower', 'Loans', 'Current', 'Overdue', 'Last checkout'],
                [
                    [
                        row['borrower'],
                        row['total_loans'],
                        row['active_loans'],
                        row['overdue_loans'],
                        row['last_checkout_at'],
                    ]
                    for row in summary['top_borrowers']
                ],
            )
        )
    else:
        lines.append('_No borrower history yet._')

    return '\n'.join(lines).rstrip()



def _render_metric_card(label, value, subtitle=None):
    subtitle_html = f'<div class="metric-subtitle">{escape(subtitle)}</div>' if subtitle else ''
    return (
        '<article class="metric-card">'
        f'<span class="metric-label">{escape(label)}</span>'
        f'<strong class="metric-value">{escape(str(value))}</strong>'
        f'{subtitle_html}'
        '</article>'
    )



def _status_badge_class(status):
    return {
        'active': 'status-active',
        'overdue': 'status-overdue',
        'returned': 'status-returned',
        'checkout': 'status-checkout',
        'return': 'status-returned',
    }.get(status, 'status-neutral')



def render_dashboard_html(snapshot):
    summary = snapshot['summary']
    current_note = ''
    if snapshot['current_loans'] and len(snapshot['current_loans']) < snapshot['current_total']:
        current_note = (
            f'<p class="section-note">Showing {len(snapshot["current_loans"])} of '
            f'{snapshot["current_total"]} currently checked-out books.</p>'
        )

    current_rows = ''.join(
        (
            '<tr>'
            f'<td><span class="status-pill {_status_badge_class(row["loan_status"])}">{escape(describe_loan_status(row))}</span></td>'
            f'<td><strong>#{row["book_id"]}</strong> {escape(row["title"])}<div class="muted">{escape(row["author"])} </div></td>'
            f'<td>{escape(row["borrower"])}</td>'
            f'<td>{escape(row["checked_out_at"])}</td>'
            f'<td>{escape(row["due_date"])}</td>'
            f'<td>{escape(str(row["loan_days"]))}d</td>'
            '</tr>'
        )
        for row in snapshot['current_loans']
    )
    if not current_rows:
        current_rows = '<tr><td colspan="6" class="empty-state">No books are currently checked out.</td></tr>'

    activity_rows = ''.join(
        (
            '<tr>'
            f'<td>{escape(row["activity_at"])}</td>'
            f'<td><span class="status-pill {_status_badge_class(row["activity_kind"])}">{escape(row["activity_kind"])}</span></td>'
            f'<td><strong>#{row["book_id"]}</strong> {escape(row["title"])}<div class="muted">{escape(row["author"])} </div></td>'
            f'<td>{escape(row["borrower"])}</td>'
            f'<td>{escape(describe_loan_status(row))}</td>'
            '</tr>'
        )
        for row in snapshot['recent_activity']
    )
    if not activity_rows:
        activity_rows = '<tr><td colspan="5" class="empty-state">No loan activity yet.</td></tr>'

    borrower_rows = ''.join(
        (
            '<tr>'
            f'<td>{escape(row["borrower"])}</td>'
            f'<td>{row["total_loans"]}</td>'
            f'<td>{row["active_loans"]}</td>'
            f'<td>{row["overdue_loans"]}</td>'
            f'<td>{escape(row["last_checkout_at"] or "-")}</td>'
            '</tr>'
        )
        for row in summary['top_borrowers']
    )
    if not borrower_rows:
        borrower_rows = '<tr><td colspan="5" class="empty-state">No borrower history yet.</td></tr>'

    attention_html = (
        '<section class="attention attention-warning">'
        f'<strong>Attention:</strong> {summary["overdue_loans"]} overdue loan(s) need follow-up in this snapshot.'
        '</section>'
        if summary['overdue_loans']
        else '<section class="attention attention-ok"><strong>Snapshot status:</strong> No overdue loans right now.</section>'
    )

    metric_cards = ''.join(
        [
            _render_metric_card('Books', summary['total_books']),
            _render_metric_card('Borrowers', summary['total_borrowers']),
            _render_metric_card('Current loans', summary['active_loans']),
            _render_metric_card('Overdue loans', summary['overdue_loans']),
            _render_metric_card('Returned loans', summary['completed_loans']),
            _render_metric_card('Late returns', summary['late_returns']),
            _render_metric_card('Avg configured loan', _format_days_metric(summary['average_configured_loan_days'])),
            _render_metric_card('Avg actual return', _format_days_metric(summary['average_return_days'])),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(snapshot['title'])}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f7fb;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --border: #d6deeb;
      --shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
      --blue: #1d4ed8;
      --blue-soft: #dbeafe;
      --amber: #b45309;
      --amber-soft: #fef3c7;
      --green: #166534;
      --green-soft: #dcfce7;
      --slate-soft: #e5e7eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #eef4ff 0%, var(--bg) 240px);
      color: var(--text);
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 40px 20px 56px;
    }}
    .hero {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: var(--shadow);
    }}
    .hero h1 {{ margin: 0 0 10px; font-size: 2.2rem; }}
    .hero p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      margin-top: 18px;
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 22px;
    }}
    .metric-card {{
      background: #f8fbff;
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
      min-height: 104px;
    }}
    .metric-label {{
      display: block;
      color: var(--muted);
      font-size: 0.92rem;
      margin-bottom: 10px;
    }}
    .metric-value {{
      display: block;
      font-size: 1.8rem;
      line-height: 1.1;
    }}
    .metric-subtitle {{
      color: var(--muted);
      font-size: 0.9rem;
      margin-top: 8px;
    }}
    .attention {{
      margin-top: 20px;
      border-radius: 18px;
      padding: 14px 16px;
      border: 1px solid transparent;
      font-weight: 600;
    }}
    .attention-warning {{
      background: var(--amber-soft);
      border-color: #f5d58a;
      color: #92400e;
    }}
    .attention-ok {{
      background: var(--green-soft);
      border-color: #9adeb6;
      color: var(--green);
    }}
    .panel {{
      margin-top: 24px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 22px;
      box-shadow: var(--shadow);
    }}
    .panel h2 {{ margin: 0 0 6px; font-size: 1.35rem; }}
    .section-note {{ margin: 0 0 16px; color: var(--muted); }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
    caption {{ text-align: left; font-weight: 700; margin-bottom: 10px; }}
    th, td {{ padding: 12px 10px; border-top: 1px solid #e5ecf6; vertical-align: top; text-align: left; }}
    th {{ color: var(--muted); font-size: 0.88rem; letter-spacing: 0.01em; }}
    tbody tr:hover {{ background: #f8fbff; }}
    .muted {{ color: var(--muted); font-size: 0.92rem; margin-top: 4px; }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 0.85rem;
      font-weight: 700;
      border: 1px solid transparent;
      white-space: nowrap;
    }}
    .status-active {{ background: var(--blue-soft); color: var(--blue); border-color: #bfd7ff; }}
    .status-overdue {{ background: var(--amber-soft); color: #92400e; border-color: #f5d58a; }}
    .status-returned {{ background: var(--green-soft); color: var(--green); border-color: #9adeb6; }}
    .status-checkout {{ background: #e0e7ff; color: #4338ca; border-color: #c7d2fe; }}
    .status-neutral {{ background: var(--slate-soft); color: #334155; border-color: #cbd5e1; }}
    .empty-state {{ color: var(--muted); font-style: italic; }}
    @media (max-width: 800px) {{
      main {{ padding: 24px 12px 40px; }}
      .hero, .panel {{ padding: 18px; border-radius: 18px; }}
      th, td {{ padding: 10px 8px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>{escape(snapshot['title'])}</h1>
      <p>Static circulation snapshot for the SQLite-backed library CLI. Use it as a recruiter-friendly artifact that highlights current checkouts, recent activity, and borrower-level trends without opening the database manually.</p>
      <div class="meta">
        <span><strong>Snapshot date:</strong> <time datetime="{escape(snapshot['reference_date'])}">{escape(snapshot['reference_date'])}</time></span>
        <span><strong>Generated at:</strong> <time datetime="{escape(snapshot['generated_at'])}">{escape(snapshot['generated_at'])}</time></span>
      </div>
      <div class="metric-grid">{metric_cards}</div>
      {attention_html}
    </section>

    <section class="panel">
      <h2>Current circulation</h2>
      {current_note}
      <table>
        <caption>Books currently checked out at the snapshot date</caption>
        <thead>
          <tr>
            <th scope="col">Status</th>
            <th scope="col">Book</th>
            <th scope="col">Borrower</th>
            <th scope="col">Checked out</th>
            <th scope="col">Due</th>
            <th scope="col">Loan days</th>
          </tr>
        </thead>
        <tbody>{current_rows}</tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Recent activity</h2>
      <table>
        <caption>Latest checkouts and returns</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Event</th>
            <th scope="col">Book</th>
            <th scope="col">Borrower</th>
            <th scope="col">Outcome</th>
          </tr>
        </thead>
        <tbody>{activity_rows}</tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Top borrowers</h2>
      <table>
        <caption>Borrower-level circulation summary</caption>
        <thead>
          <tr>
            <th scope="col">Borrower</th>
            <th scope="col">Loans</th>
            <th scope="col">Current</th>
            <th scope="col">Overdue</th>
            <th scope="col">Last checkout</th>
          </tr>
        </thead>
        <tbody>{borrower_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""



def build_trend_snapshot(
    library,
    start_date=None,
    end_date=None,
    title='Library circulation trends',
    generated_at=None,
):
    points = library.circulation_trends(start_date=start_date, end_date=end_date)
    return {
        'title': title.strip() or 'Library circulation trends',
        'generated_at': generated_at or _utc_timestamp_iso(),
        'start_date': points[0]['date'],
        'end_date': points[-1]['date'],
        'days': len(points),
        'points': points,
        'summary': {
            'peak_active_loans': max(point['active_loans'] for point in points),
            'peak_overdue_loans': max(point['overdue_loans'] for point in points),
            'total_checkouts_started': sum(point['checkouts_started'] for point in points),
            'total_returns_completed': sum(point['returns_completed'] for point in points),
        },
    }


def build_borrower_trend_snapshot(
    library,
    start_date=None,
    end_date=None,
    top_limit=4,
    title='Library borrower trend breakdown',
    generated_at=None,
):
    snapshot = library.borrower_trend_breakdown(
        start_date=start_date,
        end_date=end_date,
        top_limit=top_limit,
    )
    color_map = {
        borrower: BORROWER_TREND_COLORS[index % len(BORROWER_TREND_COLORS)]
        for index, borrower in enumerate(snapshot['borrowers'])
    }
    return {
        'title': title.strip() or 'Library borrower trend breakdown',
        'generated_at': generated_at or _utc_timestamp_iso(),
        'start_date': snapshot['start_date'],
        'end_date': snapshot['end_date'],
        'days': len(snapshot['points']),
        'top_limit': top_limit,
        'borrowers': [
            {
                **row,
                'color': color_map[row['borrower']],
            }
            for row in snapshot['summary']
        ],
        'points': snapshot['points'],
    }


def build_genre_trend_snapshot(
    library,
    start_date=None,
    end_date=None,
    top_limit=4,
    title='Library genre trend breakdown',
    generated_at=None,
):
    snapshot = library.genre_trend_breakdown(
        start_date=start_date,
        end_date=end_date,
        top_limit=top_limit,
    )
    color_map = {
        genre: GENRE_TREND_COLORS[index % len(GENRE_TREND_COLORS)]
        for index, genre in enumerate(snapshot['genres'])
    }
    return {
        'title': title.strip() or 'Library genre trend breakdown',
        'generated_at': generated_at or _utc_timestamp_iso(),
        'start_date': snapshot['start_date'],
        'end_date': snapshot['end_date'],
        'days': len(snapshot['points']),
        'top_limit': top_limit,
        'genres': [
            {
                **row,
                'color': color_map[row['genre']],
            }
            for row in snapshot['summary']
        ],
        'points': snapshot['points'],
    }


def build_genre_heatmap_snapshot(
    library,
    start_date=None,
    end_date=None,
    top_limit=4,
    title='Library genre activity heatmap',
    generated_at=None,
):
    snapshot = build_genre_trend_snapshot(
        library,
        start_date=start_date,
        end_date=end_date,
        top_limit=top_limit,
        title=title,
        generated_at=generated_at,
    )

    share_totals = {row['genre']: 0.0 for row in snapshot['genres']}
    activity_totals = {row['genre']: 0 for row in snapshot['genres']}
    max_active_loans = 0
    max_active_share = 0.0
    total_loans_touching_range = sum(row['total_loans'] for row in snapshot['genres'])

    points = []
    for point in snapshot['points']:
        total_active_selected = sum(entry['active_loans'] for entry in point['genres'])
        genre_cells = []
        for entry in point['genres']:
            active_share = entry['active_loans'] / total_active_selected if total_active_selected else 0.0
            share_totals[entry['genre']] += active_share
            activity_totals[entry['genre']] += entry['active_loans']
            max_active_loans = max(max_active_loans, entry['active_loans'])
            max_active_share = max(max_active_share, active_share)
            genre_cells.append(
                {
                    **entry,
                    'active_share': active_share,
                    'total_active_selected': total_active_selected,
                }
            )
        points.append(
            {
                'date': point['date'],
                'total_active_selected': total_active_selected,
                'genres': genre_cells,
            }
        )

    days = len(points)
    genres = []
    for row in snapshot['genres']:
        average_active_share = share_totals[row['genre']] / days if days else 0.0
        genres.append(
            {
                **row,
                'total_active_loan_days': activity_totals[row['genre']],
                'average_active_share': average_active_share,
            }
        )

    return {
        'title': title.strip() or 'Library genre activity heatmap',
        'generated_at': snapshot['generated_at'],
        'start_date': snapshot['start_date'],
        'end_date': snapshot['end_date'],
        'days': days,
        'top_limit': top_limit,
        'genres': genres,
        'points': points,
        'summary': {
            'selected_genres': len(genres),
            'max_active_loans': max_active_loans,
            'max_active_share': max_active_share,
            'total_loans_touching_range': total_loans_touching_range,
        },
    }


def build_genre_share_snapshot(
    library,
    start_date=None,
    end_date=None,
    top_limit=4,
    title='Library genre share breakdown',
    generated_at=None,
):
    snapshot = build_genre_heatmap_snapshot(
        library,
        start_date=start_date,
        end_date=end_date,
        top_limit=top_limit,
        title=title,
        generated_at=generated_at,
    )
    genre_order = {row['genre']: index for index, row in enumerate(snapshot['genres'])}
    genre_metrics = {
        row['genre']: {
            'dominant_days': 0,
            'max_daily_share': 0.0,
        }
        for row in snapshot['genres']
    }
    days_with_activity = 0
    dominant_switches = 0
    previous_dominant = None
    max_total_active_selected = 0
    max_daily_share = 0.0
    points = []

    for point in snapshot['points']:
        total_active_selected = point['total_active_selected']
        max_total_active_selected = max(max_total_active_selected, total_active_selected)
        dominant_entry = None
        if total_active_selected:
            days_with_activity += 1
            max_share_for_day = max(entry['active_share'] for entry in point['genres'])
            max_daily_share = max(max_daily_share, max_share_for_day)
            dominant_candidates = [
                entry for entry in point['genres'] if abs(entry['active_share'] - max_share_for_day) < 1e-9
            ]
            if len(dominant_candidates) == 1:
                dominant_entry = dominant_candidates[0]
                dominant_genre = dominant_entry['genre']
                genre_metrics[dominant_genre]['dominant_days'] += 1
                if previous_dominant is not None and dominant_genre != previous_dominant:
                    dominant_switches += 1
                previous_dominant = dominant_genre

        cumulative_share = 0.0
        genre_segments = []
        for entry in point['genres']:
            share_start = cumulative_share
            share_end = min(1.0, cumulative_share + entry['active_share'])
            cumulative_share = share_end
            genre_metrics[entry['genre']]['max_daily_share'] = max(
                genre_metrics[entry['genre']]['max_daily_share'],
                entry['active_share'],
            )
            genre_segments.append(
                {
                    **entry,
                    'share_start': share_start,
                    'share_end': share_end,
                    'is_dominant': bool(dominant_entry and entry['genre'] == dominant_entry['genre']),
                }
            )

        points.append(
            {
                'date': point['date'],
                'total_active_selected': total_active_selected,
                'dominant_genre': dominant_entry['genre'] if dominant_entry else None,
                'genres': genre_segments,
            }
        )

    genres = [
        {
            **row,
            'dominant_days': genre_metrics[row['genre']]['dominant_days'],
            'max_daily_share': genre_metrics[row['genre']]['max_daily_share'],
        }
        for row in snapshot['genres']
    ]

    return {
        'title': title.strip() or 'Library genre share breakdown',
        'generated_at': snapshot['generated_at'],
        'start_date': snapshot['start_date'],
        'end_date': snapshot['end_date'],
        'days': snapshot['days'],
        'top_limit': top_limit,
        'genres': genres,
        'points': points,
        'summary': {
            'selected_genres': len(genres),
            'days_with_activity': days_with_activity,
            'max_total_active_selected': max_total_active_selected,
            'max_daily_share': max_daily_share,
            'dominant_switches': dominant_switches,
            'total_loans_touching_range': snapshot['summary']['total_loans_touching_range'],
        },
    }


def render_trends_csv(snapshot):
    headers = [
        'date',
        'active_loans',
        'overdue_loans',
        'completed_loans',
        'late_returns',
        'checkouts_started',
        'returns_completed',
    ]
    lines = [','.join(headers)]
    for row in snapshot['points']:
        lines.append(','.join(str(row[header]) for header in headers))
    return '\n'.join(lines).rstrip()


def render_borrower_trends_csv(snapshot):
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow([
        'date',
        'borrower',
        'active_loans',
        'overdue_loans',
        'checkouts_started',
        'returns_completed',
    ])
    for point in snapshot['points']:
        for borrower in point['borrowers']:
            writer.writerow(
                [
                    point['date'],
                    borrower['borrower'],
                    borrower['active_loans'],
                    borrower['overdue_loans'],
                    borrower['checkouts_started'],
                    borrower['returns_completed'],
                ]
            )
    return buffer.getvalue().rstrip()


def render_genre_trends_csv(snapshot):
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow([
        'date',
        'genre',
        'active_loans',
        'overdue_loans',
        'checkouts_started',
        'returns_completed',
    ])
    for point in snapshot['points']:
        for genre in point['genres']:
            writer.writerow(
                [
                    point['date'],
                    genre['genre'],
                    genre['active_loans'],
                    genre['overdue_loans'],
                    genre['checkouts_started'],
                    genre['returns_completed'],
                ]
            )
    return buffer.getvalue().rstrip()


def render_genre_heatmap_csv(snapshot):
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow([
        'date',
        'genre',
        'active_loans',
        'active_share',
        'total_active_selected',
        'overdue_loans',
        'checkouts_started',
        'returns_completed',
    ])
    for point in snapshot['points']:
        for genre in point['genres']:
            writer.writerow(
                [
                    point['date'],
                    genre['genre'],
                    genre['active_loans'],
                    f'{genre["active_share"]:.4f}',
                    point['total_active_selected'],
                    genre['overdue_loans'],
                    genre['checkouts_started'],
                    genre['returns_completed'],
                ]
            )
    return buffer.getvalue().rstrip()


def render_genre_share_csv(snapshot):
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow([
        'date',
        'genre',
        'active_loans',
        'active_share',
        'share_start',
        'share_end',
        'total_active_selected',
        'is_dominant',
        'overdue_loans',
        'checkouts_started',
        'returns_completed',
    ])
    for point in snapshot['points']:
        for genre in point['genres']:
            writer.writerow(
                [
                    point['date'],
                    genre['genre'],
                    genre['active_loans'],
                    f'{genre["active_share"]:.4f}',
                    f'{genre["share_start"]:.4f}',
                    f'{genre["share_end"]:.4f}',
                    point['total_active_selected'],
                    1 if genre['is_dominant'] else 0,
                    genre['overdue_loans'],
                    genre['checkouts_started'],
                    genre['returns_completed'],
                ]
            )
    return buffer.getvalue().rstrip()


def _trend_x(index, count, left, width):
    if count <= 1:
        return left + width / 2
    return left + (index * width / (count - 1))


def _trend_y(value, max_value, top, height):
    scale_max = max(max_value, 1)
    return top + height - ((value / scale_max) * height)


def _render_trend_panel(snapshot, metric_key, label, color, left, top, width, height, panel_id):
    points = snapshot['points']
    values = [point[metric_key] for point in points]
    max_value = max(values) if values else 0
    chart_left = left + 52
    chart_top = top + 42
    chart_width = width - 78
    chart_height = height - 82
    baseline_y = chart_top + chart_height
    mid_value = max((max_value + 1) // 2, 1) if max_value else 0
    y_ticks = [0]
    if max_value > 1 and mid_value not in {0, max_value}:
        y_ticks.append(mid_value)
    if max_value not in {0, y_ticks[-1]}:
        y_ticks.append(max_value)

    polyline = ' '.join(
        f'{_trend_x(index, len(points), chart_left, chart_width):.2f},{_trend_y(value, max_value, chart_top, chart_height):.2f}'
        for index, value in enumerate(values)
    )
    circles = ''.join(
        (
            f'<circle cx="{_trend_x(index, len(points), chart_left, chart_width):.2f}" '
            f'cy="{_trend_y(value, max_value, chart_top, chart_height):.2f}" r="3.5" fill="{color}">'
            f'<title>{escape(label)} on {escape(points[index]["date"])}: {value}</title>'
            '</circle>'
        )
        for index, value in enumerate(values)
    )
    grid_lines = ''.join(
        (
            f'<line x1="{chart_left:.2f}" y1="{_trend_y(tick, max_value, chart_top, chart_height):.2f}" '
            f'x2="{chart_left + chart_width:.2f}" y2="{_trend_y(tick, max_value, chart_top, chart_height):.2f}" '
            'stroke="#dbe4f0" stroke-width="1" />'
            f'<text x="{left + 14:.2f}" y="{_trend_y(tick, max_value, chart_top, chart_height) + 4:.2f}" '
            'font-size="12" fill="#64748b">'
            f'{escape(str(tick))}'
            '</text>'
        )
        for tick in y_ticks
    )
    first_date = points[0]['date']
    mid_date = points[len(points) // 2]['date']
    last_date = points[-1]['date']
    axis_labels = ''.join(
        (
            f'<text x="{x:.2f}" y="{top + height - 16:.2f}" font-size="12" fill="#64748b" '
            f'text-anchor="{anchor}">{escape(label_text)}</text>'
        )
        for x, label_text, anchor in [
            (chart_left, first_date, 'start'),
            (chart_left + chart_width / 2, mid_date, 'middle'),
            (chart_left + chart_width, last_date, 'end'),
        ]
    )
    latest_value = values[-1] if values else 0
    title_id = f'{panel_id}-title'
    desc_id = f'{panel_id}-desc'
    return (
        f'<g role="group" aria-labelledby="{title_id}" aria-describedby="{desc_id}">'
        f'<title id="{title_id}">{escape(label)}</title>'
        f'<desc id="{desc_id}">Daily {escape(label.lower())} from {escape(snapshot["start_date"])} '
        f'to {escape(snapshot["end_date"])}. Peak value {max_value}, latest value {latest_value}.</desc>'
        f'<rect x="{left:.2f}" y="{top:.2f}" width="{width:.2f}" height="{height:.2f}" '
        'rx="22" fill="#ffffff" stroke="#d6deeb" />'
        f'<text x="{left + 18:.2f}" y="{top + 28:.2f}" font-size="18" font-weight="700" fill="#0f172a">{escape(label)}</text>'
        f'<text x="{left + width - 18:.2f}" y="{top + 28:.2f}" font-size="13" font-weight="600" fill="{color}" text-anchor="end">latest {latest_value}</text>'
        f'{grid_lines}'
        f'<line x1="{chart_left:.2f}" y1="{baseline_y:.2f}" x2="{chart_left + chart_width:.2f}" y2="{baseline_y:.2f}" stroke="#94a3b8" stroke-width="1.2" />'
        f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{polyline}" />'
        f'{circles}'
        f'{axis_labels}'
        '</g>'
    )


def _render_borrower_trend_panel(snapshot, metric_key, label, left, top, width, height, panel_id):
    chart_left = left + 52
    chart_top = top + 42
    chart_width = width - 78
    chart_height = height - 82
    baseline_y = chart_top + chart_height
    max_value = 0
    series = []
    for borrower in snapshot['borrowers']:
        values = []
        for point in snapshot['points']:
            row = next(item for item in point['borrowers'] if item['borrower'] == borrower['borrower'])
            values.append(row[metric_key])
        max_value = max(max_value, max(values, default=0))
        series.append({'borrower': borrower['borrower'], 'color': borrower['color'], 'values': values})

    mid_value = max((max_value + 1) // 2, 1) if max_value else 0
    y_ticks = [0]
    if max_value > 1 and mid_value not in {0, max_value}:
        y_ticks.append(mid_value)
    if max_value not in {0, y_ticks[-1]}:
        y_ticks.append(max_value)

    grid_lines = ''.join(
        (
            f'<line x1="{chart_left:.2f}" y1="{_trend_y(tick, max_value, chart_top, chart_height):.2f}" '
            f'x2="{chart_left + chart_width:.2f}" y2="{_trend_y(tick, max_value, chart_top, chart_height):.2f}" '
            'stroke="#dbe4f0" stroke-width="1" />'
            f'<text x="{left + 14:.2f}" y="{_trend_y(tick, max_value, chart_top, chart_height) + 4:.2f}" '
            'font-size="12" fill="#64748b">'
            f'{escape(str(tick))}'
            '</text>'
        )
        for tick in y_ticks
    )

    series_markup = ''.join(
        (
            f'<polyline fill="none" stroke="{series_entry["color"]}" stroke-width="3" '
            'stroke-linecap="round" stroke-linejoin="round" '
            f'points="{' '.join(
                f'{_trend_x(index, len(snapshot["points"]), chart_left, chart_width):.2f},{_trend_y(value, max_value, chart_top, chart_height):.2f}'
                for index, value in enumerate(series_entry["values"])
            )}" />'
            + ''.join(
                (
                    f'<circle cx="{_trend_x(index, len(snapshot["points"]), chart_left, chart_width):.2f}" '
                    f'cy="{_trend_y(value, max_value, chart_top, chart_height):.2f}" r="3.5" fill="{series_entry["color"]}">'
                    f'<title>{escape(series_entry["borrower"])} {escape(label.lower())} on '
                    f'{escape(snapshot["points"][index]["date"])}: {value}</title>'
                    '</circle>'
                )
                for index, value in enumerate(series_entry['values'])
            )
        )
        for series_entry in series
    )

    first_date = snapshot['points'][0]['date']
    mid_date = snapshot['points'][len(snapshot['points']) // 2]['date']
    last_date = snapshot['points'][-1]['date']
    axis_labels = ''.join(
        (
            f'<text x="{x:.2f}" y="{top + height - 16:.2f}" font-size="12" fill="#64748b" '
            f'text-anchor="{anchor}">{escape(label_text)}</text>'
        )
        for x, label_text, anchor in [
            (chart_left, first_date, 'start'),
            (chart_left + chart_width / 2, mid_date, 'middle'),
            (chart_left + chart_width, last_date, 'end'),
        ]
    )

    title_id = f'{panel_id}-title'
    desc_id = f'{panel_id}-desc'
    return (
        f'<g role="group" aria-labelledby="{title_id}" aria-describedby="{desc_id}">'
        f'<title id="{title_id}">{escape(label)}</title>'
        f'<desc id="{desc_id}">Daily {escape(label.lower())} for the top {len(snapshot["borrowers"])} borrower cohorts '
        f'from {escape(snapshot["start_date"])} to {escape(snapshot["end_date"])}. Peak value {max_value}.</desc>'
        f'<rect x="{left:.2f}" y="{top:.2f}" width="{width:.2f}" height="{height:.2f}" '
        'rx="22" fill="#ffffff" stroke="#d6deeb" />'
        f'<text x="{left + 18:.2f}" y="{top + 28:.2f}" font-size="18" font-weight="700" fill="#0f172a">{escape(label)}</text>'
        f'{grid_lines}'
        f'<line x1="{chart_left:.2f}" y1="{baseline_y:.2f}" x2="{chart_left + chart_width:.2f}" y2="{baseline_y:.2f}" stroke="#94a3b8" stroke-width="1.2" />'
        f'{series_markup}'
        f'{axis_labels}'
        '</g>'
    )


def _render_genre_trend_panel(snapshot, metric_key, label, left, top, width, height, panel_id):
    chart_left = left + 52
    chart_top = top + 42
    chart_width = width - 78
    chart_height = height - 82
    baseline_y = chart_top + chart_height
    max_value = 0
    series = []
    for genre in snapshot['genres']:
        values = []
        for point in snapshot['points']:
            row = next(item for item in point['genres'] if item['genre'] == genre['genre'])
            values.append(row[metric_key])
        max_value = max(max_value, max(values, default=0))
        series.append({'genre': genre['genre'], 'color': genre['color'], 'values': values})

    mid_value = max((max_value + 1) // 2, 1) if max_value else 0
    y_ticks = [0]
    if max_value > 1 and mid_value not in {0, max_value}:
        y_ticks.append(mid_value)
    if max_value not in {0, y_ticks[-1]}:
        y_ticks.append(max_value)

    grid_lines = ''.join(
        (
            f'<line x1="{chart_left:.2f}" y1="{_trend_y(tick, max_value, chart_top, chart_height):.2f}" '
            f'x2="{chart_left + chart_width:.2f}" y2="{_trend_y(tick, max_value, chart_top, chart_height):.2f}" '
            'stroke="#dbe4f0" stroke-width="1" />'
            f'<text x="{left + 14:.2f}" y="{_trend_y(tick, max_value, chart_top, chart_height) + 4:.2f}" '
            'font-size="12" fill="#64748b">'
            f'{escape(str(tick))}'
            '</text>'
        )
        for tick in y_ticks
    )

    series_markup = ''.join(
        (
            f'<polyline fill="none" stroke="{series_entry["color"]}" stroke-width="3" '
            'stroke-linecap="round" stroke-linejoin="round" '
            f'points="{' '.join(
                f'{_trend_x(index, len(snapshot["points"]), chart_left, chart_width):.2f},{_trend_y(value, max_value, chart_top, chart_height):.2f}'
                for index, value in enumerate(series_entry["values"])
            )}" />'
            + ''.join(
                (
                    f'<circle cx="{_trend_x(index, len(snapshot["points"]), chart_left, chart_width):.2f}" '
                    f'cy="{_trend_y(value, max_value, chart_top, chart_height):.2f}" r="3.5" fill="{series_entry["color"]}">'
                    f'<title>{escape(series_entry["genre"])} {escape(label.lower())} on '
                    f'{escape(snapshot["points"][index]["date"])}: {value}</title>'
                    '</circle>'
                )
                for index, value in enumerate(series_entry['values'])
            )
        )
        for series_entry in series
    )

    first_date = snapshot['points'][0]['date']
    mid_date = snapshot['points'][len(snapshot['points']) // 2]['date']
    last_date = snapshot['points'][-1]['date']
    axis_labels = ''.join(
        (
            f'<text x="{x:.2f}" y="{top + height - 16:.2f}" font-size="12" fill="#64748b" '
            f'text-anchor="{anchor}">{escape(label_text)}</text>'
        )
        for x, label_text, anchor in [
            (chart_left, first_date, 'start'),
            (chart_left + chart_width / 2, mid_date, 'middle'),
            (chart_left + chart_width, last_date, 'end'),
        ]
    )

    title_id = f'{panel_id}-title'
    desc_id = f'{panel_id}-desc'
    return (
        f'<g role="group" aria-labelledby="{title_id}" aria-describedby="{desc_id}">'
        f'<title id="{title_id}">{escape(label)}</title>'
        f'<desc id="{desc_id}">Daily {escape(label.lower())} for the top {len(snapshot["genres"])} genres '
        f'from {escape(snapshot["start_date"])} to {escape(snapshot["end_date"])}. Peak value {max_value}.</desc>'
        f'<rect x="{left:.2f}" y="{top:.2f}" width="{width:.2f}" height="{height:.2f}" '
        'rx="22" fill="#ffffff" stroke="#d6deeb" />'
        f'<text x="{left + 18:.2f}" y="{top + 28:.2f}" font-size="18" font-weight="700" fill="#0f172a">{escape(label)}</text>'
        f'{grid_lines}'
        f'<line x1="{chart_left:.2f}" y1="{baseline_y:.2f}" x2="{chart_left + chart_width:.2f}" y2="{baseline_y:.2f}" stroke="#94a3b8" stroke-width="1.2" />'
        f'{series_markup}'
        f'{axis_labels}'
        '</g>'
    )


def render_borrower_trends_svg(snapshot):
    title_id = 'library-borrower-trends-title'
    desc_id = 'library-borrower-trends-desc'

    legend_markup = ''.join(
        (
            f'<rect x="{40 + (index % 2) * 320:.2f}" y="{126 + (index // 2) * 22:.2f}" width="16" height="16" rx="4" fill="{borrower["color"]}" />'
            f'<text x="{64 + (index % 2) * 320:.2f}" y="{139 + (index // 2) * 22:.2f}" font-size="14" fill="#334155">{escape(borrower["borrower"])}</text>'
        )
        for index, borrower in enumerate(snapshot['borrowers'])
    )
    card_width = 260
    cards_markup = ''.join(
        (
            f'<g transform="translate({40 + index * (card_width + 16)}, 160)">'
            '<rect width="260" height="90" rx="18" fill="#ffffff" stroke="#d6deeb" />'
            f'<text x="18" y="30" font-size="14" fill="#64748b">{escape(borrower["borrower"])}</text>'
            f'<text x="18" y="62" font-size="30" font-weight="700" fill="{borrower["color"]}">{borrower["total_loans"]}</text>'
            f'<text x="18" y="78" font-size="12" fill="#64748b">loans touching this range, peak active {borrower["peak_active_loans"]}</text>'
            '</g>'
        )
        for index, borrower in enumerate(snapshot['borrowers'][:4])
    )
    panels = ''.join(
        [
            _render_borrower_trend_panel(snapshot, 'active_loans', 'Active loans by borrower', 40, 274, 520, 220, 'borrower-active-panel'),
            _render_borrower_trend_panel(snapshot, 'overdue_loans', 'Overdue loans by borrower', 600, 274, 520, 220, 'borrower-overdue-panel'),
        ]
    )

    table_top = 524
    row_height = 30
    table_rows = ''.join(
        (
            f'<rect x="40" y="{table_top + 80 + index * row_height:.2f}" width="1080" height="{row_height:.2f}" '
            f'fill="{"#ffffff" if index % 2 == 0 else "#f8fafc"}" stroke="#e2e8f0" />'
            f'<text x="58" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{escape(borrower["borrower"])}</text>'
            f'<text x="380" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{borrower["total_loans"]}</text>'
            f'<text x="500" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{borrower["peak_active_loans"]}</text>'
            f'<text x="650" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{borrower["peak_overdue_loans"]}</text>'
            f'<text x="792" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{borrower["total_checkouts_started"]}</text>'
            f'<text x="932" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{borrower["total_returns_completed"]}</text>'
            f'<text x="1046" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{borrower["days_with_active_loans"]}</text>'
        )
        for index, borrower in enumerate(snapshot['borrowers'])
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="760" viewBox="0 0 1160 760" role="img" aria-labelledby="{title_id}" aria-describedby="{desc_id}">
  <title id="{title_id}">{escape(snapshot['title'])}</title>
  <desc id="{desc_id}">Borrower-level circulation trend breakdown from {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])}. The export focuses on the top {snapshot['top_limit']} borrowers by loans touching the selected range and includes active-loan and overdue-loan trend panels plus a summary table.</desc>
  <rect width="1160" height="760" fill="#f4f7fb" />
  <rect x="24" y="24" width="1112" height="712" rx="28" fill="#eef4ff" stroke="#d6deeb" />
  <text x="40" y="68" font-size="30" font-weight="700" fill="#0f172a">{escape(snapshot['title'])}</text>
  <text x="40" y="95" font-size="15" fill="#475569">Top borrower cohorts from the SQLite circulation history, exported as a static trend pack for portfolio screenshots and recruiter walkthroughs.</text>
  <text x="40" y="118" font-size="14" fill="#475569">Range: {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])} • Days: {snapshot['days']} • Generated at: {escape(snapshot['generated_at'])}</text>
  {legend_markup}
  {cards_markup}
  {panels}
  <text x="40" y="546" font-size="18" font-weight="700" fill="#0f172a">Borrower summary</text>
  <rect x="40" y="568" width="1080" height="36" rx="10" fill="#dbeafe" stroke="#bfdbfe" />
  <text x="58" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Borrower</text>
  <text x="380" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Loans</text>
  <text x="500" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Peak active</text>
  <text x="650" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Peak overdue</text>
  <text x="792" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Checkouts</text>
  <text x="932" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Returns</text>
  <text x="1046" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Active days</text>
  {table_rows}
</svg>'''


def render_genre_trends_svg(snapshot):
    title_id = 'library-genre-trends-title'
    desc_id = 'library-genre-trends-desc'
    selected_count = len(snapshot['genres'])

    legend_markup = ''.join(
        (
            f'<rect x="{40 + (index % 2) * 320:.2f}" y="{126 + (index // 2) * 22:.2f}" width="16" height="16" rx="4" fill="{genre["color"]}" />'
            f'<text x="{64 + (index % 2) * 320:.2f}" y="{139 + (index // 2) * 22:.2f}" font-size="14" fill="#334155">{escape(genre["genre"])}</text>'
        )
        for index, genre in enumerate(snapshot['genres'])
    )
    card_width = 260
    cards_markup = ''.join(
        (
            f'<g transform="translate({40 + index * (card_width + 16)}, 160)">'
            '<rect width="260" height="90" rx="18" fill="#ffffff" stroke="#d6deeb" />'
            f'<text x="18" y="30" font-size="14" fill="#64748b">{escape(genre["genre"])}</text>'
            f'<text x="18" y="62" font-size="30" font-weight="700" fill="{genre["color"]}">{genre["total_loans"]}</text>'
            f'<text x="18" y="78" font-size="12" fill="#64748b">loans touching this range, peak active {genre["peak_active_loans"]}</text>'
            '</g>'
        )
        for index, genre in enumerate(snapshot['genres'][:4])
    )
    panels = ''.join(
        [
            _render_genre_trend_panel(snapshot, 'active_loans', 'Active loans by genre', 40, 274, 520, 220, 'genre-active-panel'),
            _render_genre_trend_panel(snapshot, 'overdue_loans', 'Overdue loans by genre', 600, 274, 520, 220, 'genre-overdue-panel'),
        ]
    )

    table_top = 524
    row_height = 30
    table_rows = ''.join(
        (
            f'<rect x="40" y="{table_top + 80 + index * row_height:.2f}" width="1080" height="{row_height:.2f}" '
            f'fill="{"#ffffff" if index % 2 == 0 else "#f8fafc"}" stroke="#e2e8f0" />'
            f'<text x="58" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{escape(genre["genre"])}</text>'
            f'<text x="380" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["total_loans"]}</text>'
            f'<text x="500" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["peak_active_loans"]}</text>'
            f'<text x="650" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["peak_overdue_loans"]}</text>'
            f'<text x="792" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["total_checkouts_started"]}</text>'
            f'<text x="932" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["total_returns_completed"]}</text>'
            f'<text x="1046" y="{table_top + 100 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["days_with_active_loans"]}</text>'
        )
        for index, genre in enumerate(snapshot['genres'])
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="760" viewBox="0 0 1160 760" role="img" aria-labelledby="{title_id}" aria-describedby="{desc_id}">
  <title id="{title_id}">{escape(snapshot['title'])}</title>
  <desc id="{desc_id}">Genre-level circulation trend breakdown from {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])}. The export includes {selected_count} selected genres touching the chosen range plus active-loan and overdue-loan trend panels and a summary table.</desc>
  <rect width="1160" height="760" fill="#f4f7fb" />
  <rect x="24" y="24" width="1112" height="712" rx="28" fill="#eef4ff" stroke="#d6deeb" />
  <text x="40" y="68" font-size="30" font-weight="700" fill="#0f172a">{escape(snapshot['title'])}</text>
  <text x="40" y="95" font-size="15" fill="#475569">Top circulation genres from the SQLite loan history, exported as a static trend pack for portfolio screenshots and recruiter walkthroughs.</text>
  <text x="40" y="118" font-size="14" fill="#475569">Range: {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])} • Days: {snapshot['days']} • Generated at: {escape(snapshot['generated_at'])}</text>
  {legend_markup}
  {cards_markup}
  {panels}
  <text x="40" y="546" font-size="18" font-weight="700" fill="#0f172a">Genre summary</text>
  <rect x="40" y="568" width="1080" height="36" rx="10" fill="#dbeafe" stroke="#bfdbfe" />
  <text x="58" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Genre</text>
  <text x="380" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Loans</text>
  <text x="500" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Peak active</text>
  <text x="650" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Peak overdue</text>
  <text x="792" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Checkouts</text>
  <text x="932" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Returns</text>
  <text x="1046" y="590" font-size="13" font-weight="700" fill="#1e3a8a">Active days</text>
  {table_rows}
</svg>'''


def render_genre_heatmap_svg(snapshot):
    title_id = 'library-genre-heatmap-title'
    desc_id = 'library-genre-heatmap-desc'
    summary = snapshot['summary']
    genre_count = max(len(snapshot['genres']), 1)
    day_count = max(len(snapshot['points']), 1)
    heatmap_left = 264
    heatmap_top = 292
    heatmap_width = 520
    heatmap_height = genre_count * 48
    cell_width = min(42, heatmap_width / day_count)
    cell_height = 34
    header_step = max(1, (day_count + 7) // 8)
    canvas_height = max(620, int(heatmap_top + heatmap_height + 130))
    outer_height = canvas_height - 48

    metric_cards = [
        ('Selected genres', summary['selected_genres'], f'top limit {snapshot["top_limit"]}'),
        ('Range days', snapshot['days'], f'{snapshot["start_date"]} → {snapshot["end_date"]}'),
        ('Peak active cell', summary['max_active_loans'], 'highest single genre/day load'),
        ('Loans touching range', summary['total_loans_touching_range'], f'peak share { _format_percent(summary["max_active_share"]) }'),
    ]
    card_markup = ''.join(
        (
            f'<g transform="translate({40 + index * 270}, 126)">'
            '<rect width="240" height="88" rx="18" fill="#ffffff" stroke="#d6deeb" />'
            f'<text x="18" y="30" font-size="13" fill="#64748b">{escape(label)}</text>'
            f'<text x="18" y="64" font-size="30" font-weight="700" fill="#1d4ed8">{value}</text>'
            f'<text x="18" y="80" font-size="12" fill="#64748b">{escape(subtitle)}</text>'
            '</g>'
        )
        for index, (label, value, subtitle) in enumerate(metric_cards)
    )

    date_labels = ''.join(
        (
            f'<text x="{heatmap_left + index * cell_width + cell_width / 2:.2f}" y="{heatmap_top - 22:.2f}" '
            'font-size="11" fill="#64748b" text-anchor="middle">'
            f'{escape(point["date"][5:])}'
            '</text>'
            f'<text x="{heatmap_left + index * cell_width + cell_width / 2:.2f}" y="{heatmap_top - 8:.2f}" '
            'font-size="10" fill="#94a3b8" text-anchor="middle">'
            f'{point["total_active_selected"]}'
            '</text>'
        )
        for index, point in enumerate(snapshot['points'])
        if index in {0, len(snapshot['points']) - 1} or index % header_step == 0
    )

    row_markup = ''.join(
        ''.join(
            [
                f'<g transform="translate(0, {heatmap_top + row_index * 48:.2f})">',
                f'<rect x="40" y="0" width="112" height="34" rx="12" fill="#ffffff" stroke="#d6deeb" />',
                f'<rect x="160" y="0" width="92" height="34" rx="12" fill="#ffffff" stroke="#d6deeb" />',
                f'<circle cx="54" cy="17" r="6" fill="{genre["color"]}" />',
                f'<text x="68" y="15" font-size="13" font-weight="700" fill="#0f172a">{escape(genre["genre"])}</text>',
                f'<text x="68" y="28" font-size="11" fill="#64748b">avg share {escape(_format_percent(genre["average_active_share"]))}</text>',
                f'<text x="174" y="15" font-size="13" font-weight="700" fill="#0f172a">{genre["total_loans"]} loans</text>',
                f'<text x="174" y="28" font-size="11" fill="#64748b">peak {genre["peak_active_loans"]} • loan-days {genre["total_active_loan_days"]}</text>',
                ''.join(
                    ''.join(
                        [
                            f'<rect x="{heatmap_left + column_index * cell_width:.2f}" y="0" width="{cell_width - 3:.2f}" height="{cell_height:.2f}" ',
                            f'rx="8" fill="{_heatmap_fill(cell["active_loans"], summary["max_active_loans"])}" stroke="#ffffff">',
                            f'<title>{escape(cell["genre"])} on {escape(point["date"])}: {cell["active_loans"]} active loans, {escape(_format_percent(cell["active_share"]))} of the selected-genre activity for the day, {cell["overdue_loans"]} overdue, {cell["checkouts_started"]} checkouts, {cell["returns_completed"]} returns.</title>',
                            '</rect>',
                            f'<text x="{heatmap_left + column_index * cell_width + (cell_width - 3) / 2:.2f}" y="21.5" font-size="11" font-weight="700" fill="{_heatmap_text_fill(cell["active_loans"], summary["max_active_loans"])}" text-anchor="middle">{cell["active_loans"]}</text>',
                        ]
                    )
                    for column_index, point in enumerate(snapshot['points'])
                    for cell in point['genres']
                    if cell['genre'] == genre['genre']
                ),
                '</g>',
            ]
        )
        for row_index, genre in enumerate(snapshot['genres'])
    )

    summary_top = heatmap_top + heatmap_height + 30
    summary_rows = ''.join(
        (
            f'<rect x="40" y="{summary_top + 60 + index * 30:.2f}" width="1080" height="30" rx="8" '
            f'fill="{"#ffffff" if index % 2 == 0 else "#f8fafc"}" stroke="#e2e8f0" />'
            f'<text x="58" y="{summary_top + 79 + index * 30:.2f}" font-size="13" fill="#0f172a">{escape(genre["genre"])}</text>'
            f'<text x="380" y="{summary_top + 79 + index * 30:.2f}" font-size="13" fill="#0f172a">{genre["total_loans"]}</text>'
            f'<text x="500" y="{summary_top + 79 + index * 30:.2f}" font-size="13" fill="#0f172a">{genre["total_active_loan_days"]}</text>'
            f'<text x="650" y="{summary_top + 79 + index * 30:.2f}" font-size="13" fill="#0f172a">{genre["peak_active_loans"]}</text>'
            f'<text x="812" y="{summary_top + 79 + index * 30:.2f}" font-size="13" fill="#0f172a">{escape(_format_percent(genre["average_active_share"]))}</text>'
            f'<text x="976" y="{summary_top + 79 + index * 30:.2f}" font-size="13" fill="#0f172a">{genre["last_checkout_at"] or "-"}</text>'
        )
        for index, genre in enumerate(snapshot['genres'])
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="{canvas_height}" viewBox="0 0 1160 {canvas_height}" role="img" aria-labelledby="{title_id}" aria-describedby="{desc_id}">
  <title id="{title_id}">{escape(snapshot['title'])}</title>
  <desc id="{desc_id}">Genre heatmap from {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])}. Each row is a selected genre and each column is a day. Darker cells mean more active loans for that genre on that day, and the tooltip text also includes the genre's share of the selected activity for that day.</desc>
  <rect width="1160" height="{canvas_height}" fill="#f4f7fb" />
  <rect x="24" y="24" width="1112" height="{outer_height}" rx="28" fill="#eef4ff" stroke="#d6deeb" />
  <text x="40" y="68" font-size="30" font-weight="700" fill="#0f172a">{escape(snapshot['title'])}</text>
  <text x="40" y="95" font-size="15" fill="#475569">One-glance subject activity story for the SQLite circulation history. Labels above the grid show the date and total active selected-genre loans for that day.</text>
  <text x="40" y="116" font-size="14" fill="#475569">Range: {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])} • Days: {snapshot['days']} • Generated at: {escape(snapshot['generated_at'])}</text>
  {card_markup}
  <text x="40" y="248" font-size="18" font-weight="700" fill="#0f172a">Genre/day activity heatmap</text>
  <text x="40" y="268" font-size="12" fill="#64748b">Cell values show active-loan counts. Darker blues indicate heavier load; tooltip descriptions include per-day activity share.</text>
  {date_labels}
  {row_markup}
  <text x="40" y="{summary_top + 16:.2f}" font-size="18" font-weight="700" fill="#0f172a">Heatmap summary</text>
  <rect x="40" y="{summary_top + 22:.2f}" width="1080" height="30" rx="8" fill="#dbeafe" stroke="#bfdbfe" />
  <text x="58" y="{summary_top + 41:.2f}" font-size="13" font-weight="700" fill="#1e3a8a">Genre</text>
  <text x="380" y="{summary_top + 41:.2f}" font-size="13" font-weight="700" fill="#1e3a8a">Loans</text>
  <text x="500" y="{summary_top + 41:.2f}" font-size="13" font-weight="700" fill="#1e3a8a">Loan-days</text>
  <text x="650" y="{summary_top + 41:.2f}" font-size="13" font-weight="700" fill="#1e3a8a">Peak active</text>
  <text x="812" y="{summary_top + 41:.2f}" font-size="13" font-weight="700" fill="#1e3a8a">Avg share</text>
  <text x="976" y="{summary_top + 41:.2f}" font-size="13" font-weight="700" fill="#1e3a8a">Last checkout</text>
  {summary_rows}
</svg>'''


def render_genre_share_svg(snapshot):
    title_id = 'library-genre-share-title'
    desc_id = 'library-genre-share-desc'
    summary = snapshot['summary']
    point_count = max(len(snapshot['points']), 1)
    chart_left = 104
    chart_top = 282
    chart_width = 548
    chart_height = 280
    slot_width = chart_width / point_count
    bar_width = min(24, max(min(slot_width - 4, slot_width), 3))
    bar_offset = (slot_width - bar_width) / 2
    header_step = max(1, (len(snapshot['points']) + 7) // 8)

    metric_cards = [
        ('Selected genres', summary['selected_genres'], f'top limit {snapshot["top_limit"]}'),
        ('Days with activity', summary['days_with_activity'], f'{snapshot["start_date"]} → {snapshot["end_date"]}'),
        ('Peak selected-day load', summary['max_total_active_selected'], 'active loans across the selected genres'),
        ('Dominant switches', summary['dominant_switches'], f'peak daily share {_format_percent(summary["max_daily_share"])}'),
    ]
    card_markup = ''.join(
        (
            f'<g transform="translate({40 + index * 270}, 126)">'
            '<rect width="240" height="88" rx="18" fill="#ffffff" stroke="#d6deeb" />'
            f'<text x="18" y="30" font-size="13" fill="#64748b">{escape(label)}</text>'
            f'<text x="18" y="64" font-size="30" font-weight="700" fill="#1d4ed8">{value}</text>'
            f'<text x="18" y="80" font-size="12" fill="#64748b">{escape(subtitle)}</text>'
            '</g>'
        )
        for index, (label, value, subtitle) in enumerate(metric_cards)
    )
    legend_markup = ''.join(
        (
            f'<rect x="{704 + (index % 2) * 190:.2f}" y="{294 + (index // 2) * 26:.2f}" width="16" height="16" rx="4" fill="{genre["color"]}" />'
            f'<text x="{728 + (index % 2) * 190:.2f}" y="{307 + (index // 2) * 26:.2f}" font-size="14" fill="#334155">{escape(genre["genre"])}</text>'
        )
        for index, genre in enumerate(snapshot['genres'])
    )
    y_ticks = [0.0, 0.25, 0.5, 0.75, 1.0]
    grid_lines = ''.join(
        (
            f'<line x1="{chart_left:.2f}" y1="{chart_top + chart_height * (1 - tick):.2f}" '
            f'x2="{chart_left + chart_width:.2f}" y2="{chart_top + chart_height * (1 - tick):.2f}" '
            'stroke="#dbe4f0" stroke-width="1" />'
            f'<text x="{chart_left - 14:.2f}" y="{chart_top + chart_height * (1 - tick) + 4:.2f}" '
            'font-size="12" fill="#64748b" text-anchor="end">'
            f'{escape(_format_percent(tick))}'
            '</text>'
        )
        for tick in y_ticks
    )
    bar_markup = ''.join(
        ''.join(
            [
                ''.join(
                    (
                        f'<rect x="{chart_left + index * slot_width + bar_offset:.2f}" '
                        f'y="{chart_top + chart_height * (1 - segment["share_end"]):.2f}" '
                        f'width="{bar_width:.2f}" '
                        f'height="{max(chart_height * (segment["share_end"] - segment["share_start"]), 1.5):.2f}" '
                        f'fill="{next(row["color"] for row in snapshot["genres"] if row["genre"] == segment["genre"])}">'
                        f'<title>{escape(segment["genre"])} on {escape(point["date"])}: {segment["active_loans"]} active loans, '
                        f'{escape(_format_percent(segment["active_share"]))} of the selected-genre activity, '
                        f'{segment["overdue_loans"]} overdue, {segment["checkouts_started"]} checkouts, '
                        f'{segment["returns_completed"]} returns.</title>'
                        '</rect>'
                    )
                    for segment in point['genres']
                    if segment['active_share'] > 0
                ),
                f'<rect x="{chart_left + index * slot_width + bar_offset:.2f}" y="{chart_top:.2f}" '
                f'width="{bar_width:.2f}" height="{chart_height:.2f}" rx="10" fill="none" stroke="#cbd5e1" />',
                (
                    f'<text x="{chart_left + index * slot_width + bar_offset + bar_width / 2:.2f}" y="{chart_top - 14:.2f}" '
                    'font-size="11" fill="#475569" text-anchor="middle">'
                    f'{point["total_active_selected"]}'
                    '</text>'
                    if index in {0, len(snapshot['points']) - 1} or index % header_step == 0
                    else ''
                ),
                (
                    f'<text x="{chart_left + index * slot_width + bar_offset + bar_width / 2:.2f}" y="{chart_top + chart_height + 20:.2f}" '
                    'font-size="11" fill="#64748b" text-anchor="middle">'
                    f'{escape(point["date"][5:])}'
                    '</text>'
                    if index in {0, len(snapshot['points']) - 1} or index % header_step == 0
                    else ''
                ),
            ]
        )
        for index, point in enumerate(snapshot['points'])
    )

    summary_top = 612
    row_height = 30
    summary_rows = ''.join(
        (
            f'<rect x="40" y="{summary_top + 60 + index * row_height:.2f}" width="1080" height="{row_height:.2f}" rx="8" '
            f'fill="{"#ffffff" if index % 2 == 0 else "#f8fafc"}" stroke="#e2e8f0" />'
            f'<circle cx="58" cy="{summary_top + 79 + index * row_height:.2f}" r="6" fill="{genre["color"]}" />'
            f'<text x="74" y="{summary_top + 83 + index * row_height:.2f}" font-size="13" fill="#0f172a">{escape(genre["genre"])}</text>'
            f'<text x="366" y="{summary_top + 83 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["total_active_loan_days"]}</text>'
            f'<text x="502" y="{summary_top + 83 + index * row_height:.2f}" font-size="13" fill="#0f172a">{escape(_format_percent(genre["average_active_share"]))}</text>'
            f'<text x="646" y="{summary_top + 83 + index * row_height:.2f}" font-size="13" fill="#0f172a">{escape(_format_percent(genre["max_daily_share"]))}</text>'
            f'<text x="804" y="{summary_top + 83 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["dominant_days"]}</text>'
            f'<text x="958" y="{summary_top + 83 + index * row_height:.2f}" font-size="13" fill="#0f172a">{genre["last_checkout_at"] or "-"}</text>'
        )
        for index, genre in enumerate(snapshot['genres'])
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="820" viewBox="0 0 1160 820" role="img" aria-labelledby="{title_id}" aria-describedby="{desc_id}">
  <title id="{title_id}">{escape(snapshot['title'])}</title>
  <desc id="{desc_id}">Genre share breakdown from {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])}. Each day is a normalized stacked column showing how the selected genres share that day's active circulation. Count labels above the chart show the absolute selected-genre load for the same day.</desc>
  <rect width="1160" height="820" fill="#f4f7fb" />
  <rect x="24" y="24" width="1112" height="772" rx="28" fill="#eef4ff" stroke="#d6deeb" />
  <text x="40" y="68" font-size="30" font-weight="700" fill="#0f172a">{escape(snapshot['title'])}</text>
  <text x="40" y="95" font-size="15" fill="#475569">Normalized stacked columns show how the genre mix shifts day by day, while the labels above the bars keep the absolute circulation load visible.</text>
  <text x="40" y="116" font-size="14" fill="#475569">Range: {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])} • Days: {snapshot['days']} • Generated at: {escape(snapshot['generated_at'])}</text>
  {card_markup}
  <text x="40" y="248" font-size="18" font-weight="700" fill="#0f172a">Genre composition share</text>
  <text x="40" y="268" font-size="12" fill="#64748b">Bar height is normalized to 100%. The value above each labeled bar shows the day’s total active loans across the selected genres.</text>
  {grid_lines}
  {bar_markup}
  <text x="704" y="248" font-size="18" font-weight="700" fill="#0f172a">Legend</text>
  <text x="704" y="268" font-size="12" fill="#64748b">Top genres touching the selected range. Colors stay aligned with the existing genre trend and heatmap exports.</text>
  {legend_markup}
  <rect x="704" y="386" width="376" height="176" rx="22" fill="#ffffff" stroke="#d6deeb" />
  <text x="728" y="418" font-size="18" font-weight="700" fill="#0f172a">Composition notes</text>
  <text x="728" y="446" font-size="14" fill="#334155">• {summary['days_with_activity']} active day(s) had at least one selected-genre loan.</text>
  <text x="728" y="474" font-size="14" fill="#334155">• Peak selected-day load was {summary['max_total_active_selected']} active loan(s).</text>
  <text x="728" y="502" font-size="14" fill="#334155">• The most concentrated single-day share reached {escape(_format_percent(summary['max_daily_share']))}.</text>
  <text x="728" y="530" font-size="14" fill="#334155">• The uniquely dominant genre changed {summary['dominant_switches']} time(s); tied days do not force a winner.</text>
  <text x="40" y="630" font-size="18" font-weight="700" fill="#0f172a">Genre share summary</text>
  <rect x="40" y="636" width="1080" height="30" rx="8" fill="#dbeafe" stroke="#bfdbfe" />
  <text x="74" y="655" font-size="13" font-weight="700" fill="#1e3a8a">Genre</text>
  <text x="366" y="655" font-size="13" font-weight="700" fill="#1e3a8a">Loan-days</text>
  <text x="502" y="655" font-size="13" font-weight="700" fill="#1e3a8a">Avg share</text>
  <text x="646" y="655" font-size="13" font-weight="700" fill="#1e3a8a">Max share</text>
  <text x="804" y="655" font-size="13" font-weight="700" fill="#1e3a8a">Lead days</text>
  <text x="958" y="655" font-size="13" font-weight="700" fill="#1e3a8a">Last checkout</text>
  {summary_rows}
</svg>'''


def render_trends_svg(snapshot):
    summary = snapshot['summary']
    title_id = 'library-trends-title'
    desc_id = 'library-trends-desc'
    cards = [
        ('Peak active loans', summary['peak_active_loans'], '#2563eb'),
        ('Peak overdue loans', summary['peak_overdue_loans'], '#d97706'),
        ('Total checkouts', summary['total_checkouts_started'], '#7c3aed'),
        ('Total returns', summary['total_returns_completed'], '#059669'),
    ]
    card_markup = ''.join(
        (
            f'<g transform="translate({40 + index * 270}, 118)">'
            '<rect width="240" height="88" rx="18" fill="#ffffff" stroke="#d6deeb" />'
            f'<text x="18" y="32" font-size="13" fill="#64748b">{escape(label)}</text>'
            f'<text x="18" y="67" font-size="30" font-weight="700" fill="{color}">{value}</text>'
            '</g>'
        )
        for index, (label, value, color) in enumerate(cards)
    )
    panels = [
        ('active_loans', 'Active loans', '#2563eb', 40, 240, 'active-panel'),
        ('overdue_loans', 'Overdue loans', '#d97706', 600, 240, 'overdue-panel'),
        ('checkouts_started', 'Checkouts started', '#7c3aed', 40, 500, 'checkouts-panel'),
        ('returns_completed', 'Returns completed', '#059669', 600, 500, 'returns-panel'),
    ]
    panel_markup = ''.join(
        _render_trend_panel(snapshot, metric_key, label, color, left, top, 520, 220, panel_id)
        for metric_key, label, color, left, top, panel_id in panels
    )
    return f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1160\" height=\"760\" viewBox=\"0 0 1160 760\" role=\"img\" aria-labelledby=\"{title_id}\" aria-describedby=\"{desc_id}\">
  <title id=\"{title_id}\">{escape(snapshot['title'])}</title>
  <desc id=\"{desc_id}\">Small-multiple circulation trend charts covering {escape(snapshot['start_date'])} through {escape(snapshot['end_date'])}. The export includes active loans, overdue loans, daily checkouts, and daily returns.</desc>
  <rect width=\"1160\" height=\"760\" fill=\"#f4f7fb\" />
  <rect x=\"24\" y=\"24\" width=\"1112\" height=\"712\" rx=\"28\" fill=\"#eef4ff\" stroke=\"#d6deeb\" />
  <text x=\"40\" y=\"70\" font-size=\"30\" font-weight=\"700\" fill=\"#0f172a\">{escape(snapshot['title'])}</text>
  <text x=\"40\" y=\"98\" font-size=\"15\" fill=\"#475569\">Daily circulation analytics for a recruiter-friendly portfolio artifact, exported from the SQLite CLI without opening the database manually.</text>
  <text x=\"40\" y=\"220\" font-size=\"14\" fill=\"#475569\">Range: {escape(snapshot['start_date'])} to {escape(snapshot['end_date'])} • Days: {snapshot['days']} • Generated at: {escape(snapshot['generated_at'])}</text>
  {card_markup}
  {panel_markup}
</svg>"""


def parse_optional_date(value, label):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise LibraryError(f'{label} must use YYYY-MM-DD format') from exc



def parse_optional_timestamp(value, label):
    if not value:
        return None
    normalized = value.replace('Z', '+00:00')
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise LibraryError(f'{label} must use an ISO-8601 timestamp') from exc
    return parsed.replace(microsecond=0).isoformat().replace('+00:00', 'Z')



def main(argv=None):
    parser = argparse.ArgumentParser(description='Library manager')
    parser.add_argument('--db', default='library.db')
    sub = parser.add_subparsers(dest='cmd', required=True)

    add_parser = sub.add_parser('add', help='Add a book to the catalog')
    add_parser.add_argument('title')
    add_parser.add_argument('author')
    add_parser.add_argument('--genre', default='General')

    checkout_parser = sub.add_parser('checkout', help='Check out a book')
    checkout_parser.add_argument('book_id', type=int)
    checkout_parser.add_argument('borrower')
    checkout_parser.add_argument('--days', type=int, default=14)

    return_parser = sub.add_parser('return', help='Return a checked-out book')
    return_parser.add_argument('book_id', type=int)

    list_parser = sub.add_parser('list', help='List catalog books')
    list_parser.add_argument('--query')
    list_parser.add_argument('--search-mode', choices=['auto', 'keyword', 'fts'], default='auto')
    list_parser.add_argument('--limit', type=int)

    overdue_parser = sub.add_parser('overdue', help='List overdue books')
    overdue_parser.add_argument('--date', dest='reference_date')

    history_parser = sub.add_parser('history', help='Show loan history and active circulation records')
    history_parser.add_argument('--book-id', type=int)
    history_parser.add_argument('--borrower')
    history_parser.add_argument('--status', choices=['all', 'active', 'overdue', 'returned'], default='all')
    history_parser.add_argument('--limit', type=int)
    history_parser.add_argument('--date', dest='reference_date')

    stats_parser = sub.add_parser('stats', help='Show circulation analytics')
    stats_parser.add_argument('--date', dest='reference_date')
    stats_parser.add_argument('--top', type=int, default=5)

    trends_parser = sub.add_parser('trends', help='Export chart-friendly circulation trends')
    trends_parser.add_argument('--start-date')
    trends_parser.add_argument('--end-date')
    trends_parser.add_argument('--csv-out', type=Path)
    trends_parser.add_argument('--svg-out', type=Path)
    trends_parser.add_argument('--title', default='Library circulation trends')
    trends_parser.add_argument('--generated-at')

    borrower_trends_parser = sub.add_parser('borrower-trends', help='Export borrower-level circulation trend breakdowns')
    borrower_trends_parser.add_argument('--start-date')
    borrower_trends_parser.add_argument('--end-date')
    borrower_trends_parser.add_argument('--top', type=int, default=4)
    borrower_trends_parser.add_argument('--csv-out', type=Path)
    borrower_trends_parser.add_argument('--svg-out', type=Path)
    borrower_trends_parser.add_argument('--title', default='Library borrower trend breakdown')
    borrower_trends_parser.add_argument('--generated-at')

    genre_trends_parser = sub.add_parser('genre-trends', help='Export genre-level circulation trend breakdowns')
    genre_trends_parser.add_argument('--start-date')
    genre_trends_parser.add_argument('--end-date')
    genre_trends_parser.add_argument('--top', type=int, default=4)
    genre_trends_parser.add_argument('--csv-out', type=Path)
    genre_trends_parser.add_argument('--svg-out', type=Path)
    genre_trends_parser.add_argument('--title', default='Library genre trend breakdown')
    genre_trends_parser.add_argument('--generated-at')

    genre_heatmap_parser = sub.add_parser('genre-heatmap', help='Export a genre/day activity heatmap')
    genre_heatmap_parser.add_argument('--start-date')
    genre_heatmap_parser.add_argument('--end-date')
    genre_heatmap_parser.add_argument('--top', type=int, default=4)
    genre_heatmap_parser.add_argument('--csv-out', type=Path)
    genre_heatmap_parser.add_argument('--svg-out', type=Path)
    genre_heatmap_parser.add_argument('--title', default='Library genre activity heatmap')
    genre_heatmap_parser.add_argument('--generated-at')

    genre_share_parser = sub.add_parser('genre-share', help='Export a stacked-share genre composition view')
    genre_share_parser.add_argument('--start-date')
    genre_share_parser.add_argument('--end-date')
    genre_share_parser.add_argument('--top', type=int, default=4)
    genre_share_parser.add_argument('--csv-out', type=Path)
    genre_share_parser.add_argument('--svg-out', type=Path)
    genre_share_parser.add_argument('--title', default='Library genre share breakdown')
    genre_share_parser.add_argument('--generated-at')

    dashboard_parser = sub.add_parser('dashboard', help='Export a recruiter-friendly circulation snapshot')
    dashboard_parser.add_argument('--date', dest='reference_date')
    dashboard_parser.add_argument('--top', type=int, default=5)
    dashboard_parser.add_argument('--current-limit', type=int, default=8)
    dashboard_parser.add_argument('--recent-limit', type=int, default=8)
    dashboard_parser.add_argument('--markdown-out', type=Path)
    dashboard_parser.add_argument('--html-out', type=Path)
    dashboard_parser.add_argument('--title', default='Library circulation dashboard')
    dashboard_parser.add_argument('--generated-at')

    args = parser.parse_args(argv)
    library = Library(args.db)

    try:
        if args.cmd == 'add':
            library.add_book(args.title, args.author, genre=args.genre)
            print('book added')
        elif args.cmd == 'checkout':
            due_day = library.checkout(args.book_id, args.borrower, args.days)
            print(f'checked out until {due_day.isoformat()}')
        elif args.cmd == 'return':
            library.return_book(args.book_id)
            print('book returned')
        elif args.cmd == 'list':
            books = library.list_books(query=args.query, search_mode=args.search_mode, limit=args.limit)
            if not books:
                print('no books found')
            for row in books:
                print(format_book(row))
        elif args.cmd == 'overdue':
            ref = parse_optional_date(args.reference_date, 'reference date')
            books = library.overdue_books(ref)
            if not books:
                print('no overdue books')
            for row in books:
                print(format_book(row))
        elif args.cmd == 'history':
            ref = parse_optional_date(args.reference_date, 'reference date')
            rows = library.loan_history(
                book_id=args.book_id,
                borrower=args.borrower,
                status=args.status,
                limit=args.limit,
                reference_date=ref,
            )
            if not rows:
                print('no loan history found')
            for row in rows:
                print(format_loan(row))
        elif args.cmd == 'stats':
            ref = parse_optional_date(args.reference_date, 'reference date')
            stats = library.circulation_stats(reference_date=ref, top_limit=args.top)
            print(format_stats(stats))
        elif args.cmd == 'trends':
            start_day = parse_optional_date(args.start_date, 'start date')
            end_day = parse_optional_date(args.end_date, 'end date')
            generated_at = parse_optional_timestamp(args.generated_at, 'generated-at')
            snapshot = build_trend_snapshot(
                library,
                start_date=start_day,
                end_date=end_day,
                title=args.title,
                generated_at=generated_at,
            )
            csv_output = render_trends_csv(snapshot)
            written = []
            if args.csv_out:
                _write_text_output(args.csv_out, csv_output + '\n')
                written.append(str(args.csv_out))
            if args.svg_out:
                _write_text_output(args.svg_out, render_trends_svg(snapshot) + '\n')
                written.append(str(args.svg_out))
            if written:
                print('trend artifacts written: ' + ', '.join(written))
            else:
                print(csv_output)
        elif args.cmd == 'borrower-trends':
            start_day = parse_optional_date(args.start_date, 'start date')
            end_day = parse_optional_date(args.end_date, 'end date')
            generated_at = parse_optional_timestamp(args.generated_at, 'generated-at')
            snapshot = build_borrower_trend_snapshot(
                library,
                start_date=start_day,
                end_date=end_day,
                top_limit=args.top,
                title=args.title,
                generated_at=generated_at,
            )
            csv_output = render_borrower_trends_csv(snapshot)
            written = []
            if args.csv_out:
                _write_text_output(args.csv_out, csv_output + '\n')
                written.append(str(args.csv_out))
            if args.svg_out:
                _write_text_output(args.svg_out, render_borrower_trends_svg(snapshot) + '\n')
                written.append(str(args.svg_out))
            if written:
                print('borrower trend artifacts written: ' + ', '.join(written))
            else:
                print(csv_output)
        elif args.cmd == 'genre-trends':
            start_day = parse_optional_date(args.start_date, 'start date')
            end_day = parse_optional_date(args.end_date, 'end date')
            generated_at = parse_optional_timestamp(args.generated_at, 'generated-at')
            snapshot = build_genre_trend_snapshot(
                library,
                start_date=start_day,
                end_date=end_day,
                top_limit=args.top,
                title=args.title,
                generated_at=generated_at,
            )
            csv_output = render_genre_trends_csv(snapshot)
            written = []
            if args.csv_out:
                _write_text_output(args.csv_out, csv_output + '\n')
                written.append(str(args.csv_out))
            if args.svg_out:
                _write_text_output(args.svg_out, render_genre_trends_svg(snapshot) + '\n')
                written.append(str(args.svg_out))
            if written:
                print('genre trend artifacts written: ' + ', '.join(written))
            else:
                print(csv_output)
        elif args.cmd == 'genre-heatmap':
            start_day = parse_optional_date(args.start_date, 'start date')
            end_day = parse_optional_date(args.end_date, 'end date')
            generated_at = parse_optional_timestamp(args.generated_at, 'generated-at')
            snapshot = build_genre_heatmap_snapshot(
                library,
                start_date=start_day,
                end_date=end_day,
                top_limit=args.top,
                title=args.title,
                generated_at=generated_at,
            )
            csv_output = render_genre_heatmap_csv(snapshot)
            written = []
            if args.csv_out:
                _write_text_output(args.csv_out, csv_output + '\n')
                written.append(str(args.csv_out))
            if args.svg_out:
                _write_text_output(args.svg_out, render_genre_heatmap_svg(snapshot) + '\n')
                written.append(str(args.svg_out))
            if written:
                print('genre heatmap artifacts written: ' + ', '.join(written))
            else:
                print(csv_output)
        elif args.cmd == 'genre-share':
            start_day = parse_optional_date(args.start_date, 'start date')
            end_day = parse_optional_date(args.end_date, 'end date')
            generated_at = parse_optional_timestamp(args.generated_at, 'generated-at')
            snapshot = build_genre_share_snapshot(
                library,
                start_date=start_day,
                end_date=end_day,
                top_limit=args.top,
                title=args.title,
                generated_at=generated_at,
            )
            csv_output = render_genre_share_csv(snapshot)
            written = []
            if args.csv_out:
                _write_text_output(args.csv_out, csv_output + '\n')
                written.append(str(args.csv_out))
            if args.svg_out:
                _write_text_output(args.svg_out, render_genre_share_svg(snapshot) + '\n')
                written.append(str(args.svg_out))
            if written:
                print('genre share artifacts written: ' + ', '.join(written))
            else:
                print(csv_output)
        elif args.cmd == 'dashboard':
            ref = parse_optional_date(args.reference_date, 'reference date')
            generated_at = parse_optional_timestamp(args.generated_at, 'generated-at')
            snapshot = build_dashboard_snapshot(
                library,
                reference_date=ref,
                top_limit=args.top,
                current_limit=args.current_limit,
                recent_limit=args.recent_limit,
                title=args.title,
                generated_at=generated_at,
            )
            markdown = render_dashboard_markdown(snapshot)
            written = []
            if args.markdown_out:
                _write_text_output(args.markdown_out, markdown + '\n')
                written.append(str(args.markdown_out))
            if args.html_out:
                _write_text_output(args.html_out, render_dashboard_html(snapshot) + '\n')
                written.append(str(args.html_out))
            if written:
                print('dashboard written: ' + ', '.join(written))
            else:
                print(markdown)
    except LibraryError as exc:
        raise SystemExit(str(exc))


if __name__ == '__main__':
    main()
