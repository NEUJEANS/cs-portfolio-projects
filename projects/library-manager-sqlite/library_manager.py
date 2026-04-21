import argparse
import re
import sqlite3
from datetime import date, timedelta
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
            'WHEN l.returned_at IS NOT NULL THEN "returned" '
            'WHEN l.due_date < ? THEN "overdue" '
            'ELSE "active" '
            'END AS loan_status, '
            'CASE '
            'WHEN l.returned_at IS NOT NULL AND l.returned_at > l.due_date '
            'THEN CAST(julianday(l.returned_at) - julianday(l.due_date) AS INTEGER) '
            'WHEN l.returned_at IS NULL AND l.due_date < ? '
            'THEN CAST(julianday(?) - julianday(l.due_date) AS INTEGER) '
            'ELSE 0 '
            'END AS lateness_days '
            'FROM loans AS l '
            'JOIN books AS b ON b.id = l.book_id '
            'JOIN borrowers AS br ON br.id = l.borrower_id '
            'WHERE 1 = 1'
        )
        params = [reference_iso, reference_iso, reference_iso]

        if book_id is not None:
            sql += ' AND b.id = ?'
            params.append(book_id)
        if borrower:
            sql += ' AND lower(br.name) LIKE ?'
            params.append(f'%{borrower.lower()}%')
        if status == 'active':
            sql += ' AND l.returned_at IS NULL AND l.due_date >= ?'
            params.append(reference_iso)
        elif status == 'overdue':
            sql += ' AND l.returned_at IS NULL AND l.due_date < ?'
            params.append(reference_iso)
        elif status == 'returned':
            sql += ' AND l.returned_at IS NOT NULL'

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
                    'COALESCE(SUM(CASE WHEN returned_at IS NULL THEN 1 ELSE 0 END), 0) AS active_loans, '
                    'COALESCE(SUM(CASE WHEN returned_at IS NULL AND due_date < ? THEN 1 ELSE 0 END), 0) AS overdue_loans, '
                    'COALESCE(SUM(CASE WHEN returned_at IS NOT NULL THEN 1 ELSE 0 END), 0) AS completed_loans, '
                    'ROUND(AVG(CAST(loan_days AS REAL)), 2) AS average_configured_loan_days, '
                    'ROUND(AVG(CASE WHEN returned_at IS NOT NULL THEN julianday(returned_at) - julianday(checked_out_at) END), 2) AS average_return_days, '
                    'COALESCE(SUM(CASE WHEN returned_at IS NOT NULL AND returned_at > due_date THEN 1 ELSE 0 END), 0) AS late_returns '
                    'FROM loans',
                    (reference_iso,),
                ).fetchone()
            )
            top_borrowers = [
                dict(r)
                for r in conn.execute(
                    'SELECT '
                    'br.name AS borrower, '
                    'COUNT(*) AS total_loans, '
                    'SUM(CASE WHEN l.returned_at IS NULL THEN 1 ELSE 0 END) AS active_loans, '
                    'SUM(CASE WHEN l.returned_at IS NULL AND l.due_date < ? THEN 1 ELSE 0 END) AS overdue_loans, '
                    'MAX(l.checked_out_at) AS last_checkout_at '
                    'FROM loans AS l '
                    'JOIN borrowers AS br ON br.id = l.borrower_id '
                    'GROUP BY br.id, br.name '
                    'ORDER BY total_loans DESC, active_loans DESC, br.name COLLATE NOCASE '
                    'LIMIT ?',
                    (reference_iso, top_limit),
                )
            ]
        summary['top_borrowers'] = top_borrowers
        return summary



def format_book(row):
    state = 'available' if row['available'] else f"checked out to {row['borrower']} (due {row['due_date']})"
    rendered = f"#{row['id']} {row['title']} - {row['author']} [{state}]"
    preview = row.get('search_preview')
    if preview:
        rendered += f"\n    match: {preview}"
    return rendered



def format_loan(row):
    if row['loan_status'] == 'returned':
        status = 'returned'
        if row['lateness_days'] > 0:
            status += f" late by {row['lateness_days']}d"
        else:
            status += ' on time'
    elif row['loan_status'] == 'overdue':
        status = f"overdue by {row['lateness_days']}d"
    else:
        status = 'active'
    returned_at = row['returned_at'] or '-'
    return (
        f"loan #{row['loan_id']} | book #{row['book_id']} {row['title']} - {row['author']} | "
        f"borrower: {row['borrower']} | out {row['checked_out_at']} | due {row['due_date']} | "
        f"returned {returned_at} [{status}]"
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



def parse_optional_date(value, label):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise LibraryError(f'{label} must use YYYY-MM-DD format') from exc



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
    except LibraryError as exc:
        raise SystemExit(str(exc))


if __name__ == '__main__':
    main()
