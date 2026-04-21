import argparse
import re
import sqlite3
from datetime import date, datetime, timezone, timedelta
from html import escape
from pathlib import Path


class LibraryError(Exception):
    pass


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
                'borrower': 'ALTER TABLE books ADD COLUMN borrower TEXT',
                'checked_out_at': 'ALTER TABLE books ADD COLUMN checked_out_at TEXT',
                'due_date': 'ALTER TABLE books ADD COLUMN due_date TEXT',
            }
            for column, statement in migrations.items():
                if column not in columns:
                    conn.execute(statement)
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

    def add_book(self, title, author):
        title = title.strip()
        author = author.strip()
        if not title or not author:
            raise LibraryError('title and author are required')
        with self._connect() as conn:
            cursor = conn.execute(
                'INSERT INTO books(title, author, available, borrower, checked_out_at, due_date) '
                'VALUES (?, ?, 1, NULL, NULL, NULL)',
                (title, author),
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



def format_book(row):
    state = 'available' if row['available'] else f"checked out to {row['borrower']} (due {row['due_date']})"
    rendered = f"#{row['id']} {row['title']} - {row['author']} [{state}]"
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
            library.add_book(args.title, args.author)
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
