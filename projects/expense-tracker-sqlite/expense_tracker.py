import argparse, sqlite3
from pathlib import Path

class ExpenseTracker:
    def __init__(self, db_path='expenses.db'):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, category TEXT, amount REAL, note TEXT)')

    def add(self, category, amount, note=''):
        with self._connect() as conn:
            conn.execute('INSERT INTO expenses(category, amount, note) VALUES (?, ?, ?)', (category, amount, note))

    def list(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute('SELECT * FROM expenses ORDER BY id')]

    def total_by_category(self):
        with self._connect() as conn:
            rows = conn.execute('SELECT category, ROUND(SUM(amount), 2) total FROM expenses GROUP BY category ORDER BY total DESC')
            return [dict(r) for r in rows]


def build_parser():
    p = argparse.ArgumentParser(description='Expense tracker')
    p.add_argument('--db', default='expenses.db')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('add')
    a.add_argument('category')
    a.add_argument('amount', type=float)
    a.add_argument('--note', default='')
    sub.add_parser('list')
    sub.add_parser('summary')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    tracker = ExpenseTracker(args.db)
    if args.cmd == 'add':
        tracker.add(args.category, args.amount, args.note)
        print('expense added')
    elif args.cmd == 'list':
        for row in tracker.list():
            print(f"#{row['id']} {row['category']} ${row['amount']:.2f} {row['note']}")
    elif args.cmd == 'summary':
        for row in tracker.total_by_category():
            print(f"{row['category']}: ${row['total']:.2f}")

if __name__ == '__main__':
    main()
