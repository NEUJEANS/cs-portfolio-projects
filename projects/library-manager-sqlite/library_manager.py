import argparse
import sqlite3
from datetime import date, timedelta
from pathlib import Path


class LibraryError(Exception):
    pass


class Library:
    def __init__(self, db_path='library.db'):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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

    def add_book(self, title, author):
        title = title.strip()
        author = author.strip()
        if not title or not author:
            raise LibraryError('title and author are required')
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO books(title, author, available, borrower, checked_out_at, due_date) '
                'VALUES (?, ?, 1, NULL, NULL, NULL)',
                (title, author),
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
            conn.execute(
                'UPDATE books SET available = 0, borrower = ?, checked_out_at = ?, due_date = ? WHERE id = ?',
                (borrower, checkout_day.isoformat(), due_day.isoformat(), book_id),
            )
            return due_day

    def return_book(self, book_id):
        with self._connect() as conn:
            book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
            if not book:
                raise LibraryError(f'book #{book_id} not found')
            if book['available']:
                raise LibraryError(f'book #{book_id} is not checked out')
            conn.execute(
                'UPDATE books SET available = 1, borrower = NULL, checked_out_at = NULL, due_date = NULL WHERE id = ?',
                (book_id,),
            )

    def list_books(self, query=None):
        sql = 'SELECT * FROM books'
        params = []
        if query:
            sql += ' WHERE lower(title) LIKE ? OR lower(author) LIKE ?'
            like = f'%{query.lower()}%'
            params.extend([like, like])
        sql += ' ORDER BY id'
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(sql, params)]

    def overdue_books(self, reference_date=None):
        ref = (reference_date or date.today()).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT * FROM books WHERE available = 0 AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date, id',
                (ref,),
            )
            return [dict(r) for r in rows]


def format_book(row):
    state = 'available' if row['available'] else f"checked out to {row['borrower']} (due {row['due_date']})"
    return f"#{row['id']} {row['title']} - {row['author']} [{state}]"


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

    overdue_parser = sub.add_parser('overdue', help='List overdue books')
    overdue_parser.add_argument('--date', dest='reference_date')

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
            books = library.list_books(query=args.query)
            if not books:
                print('no books found')
            for row in books:
                print(format_book(row))
        elif args.cmd == 'overdue':
            try:
                ref = date.fromisoformat(args.reference_date) if args.reference_date else None
            except ValueError as exc:
                raise LibraryError('reference date must use YYYY-MM-DD format') from exc
            books = library.overdue_books(ref)
            if not books:
                print('no overdue books')
            for row in books:
                print(format_book(row))
    except LibraryError as exc:
        raise SystemExit(str(exc))


if __name__ == '__main__':
    main()
