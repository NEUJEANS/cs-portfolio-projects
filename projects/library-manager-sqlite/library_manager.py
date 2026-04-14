import argparse, sqlite3
from pathlib import Path

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
            conn.execute('CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, available INTEGER DEFAULT 1)')

    def add_book(self, title, author):
        with self._connect() as conn:
            conn.execute('INSERT INTO books(title, author, available) VALUES (?, ?, 1)', (title, author))

    def checkout(self, book_id):
        with self._connect() as conn:
            conn.execute('UPDATE books SET available = 0 WHERE id = ?', (book_id,))

    def list_books(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute('SELECT * FROM books ORDER BY id')]


def main(argv=None):
    p = argparse.ArgumentParser(description='Library manager')
    p.add_argument('--db', default='library.db')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('add')
    a.add_argument('title')
    a.add_argument('author')
    c = sub.add_parser('checkout')
    c.add_argument('book_id', type=int)
    sub.add_parser('list')
    args = p.parse_args(argv)
    library = Library(args.db)
    if args.cmd == 'add':
        library.add_book(args.title, args.author)
        print('book added')
    elif args.cmd == 'checkout':
        library.checkout(args.book_id)
        print('checked out')
    else:
        for row in library.list_books():
            state = 'available' if row['available'] else 'checked out'
            print(f"#{row['id']} {row['title']} - {row['author']} ({state})")

if __name__ == '__main__':
    main()
