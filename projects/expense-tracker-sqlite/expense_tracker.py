import argparse
import sqlite3
from datetime import date
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
            conn.execute(
                'CREATE TABLE IF NOT EXISTS expenses ('
                'id INTEGER PRIMARY KEY, '
                'category TEXT NOT NULL, '
                'amount REAL NOT NULL, '
                'note TEXT NOT NULL DEFAULT "", '
                'spent_on TEXT NOT NULL DEFAULT ""'
                ')'
            )
            columns = {row['name'] for row in conn.execute('PRAGMA table_info(expenses)')}
            if 'spent_on' not in columns:
                conn.execute('ALTER TABLE expenses ADD COLUMN spent_on TEXT NOT NULL DEFAULT ""')
            conn.execute(
                'UPDATE expenses SET spent_on = ? WHERE spent_on = "" OR spent_on IS NULL',
                (date.today().isoformat(),),
            )

    def _validate_category(self, category):
        cleaned = category.strip()
        if not cleaned:
            raise ValueError('category must not be empty')
        return cleaned

    def _validate_amount(self, amount):
        value = float(amount)
        if value <= 0:
            raise ValueError('amount must be greater than 0')
        return round(value, 2)

    def _validate_date(self, spent_on=None):
        if spent_on in (None, ''):
            return date.today().isoformat()
        return date.fromisoformat(spent_on).isoformat()

    def add(self, category, amount, note='', spent_on=None):
        category = self._validate_category(category)
        amount = self._validate_amount(amount)
        spent_on = self._validate_date(spent_on)
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO expenses(category, amount, note, spent_on) VALUES (?, ?, ?, ?)',
                (category, amount, note.strip(), spent_on),
            )

    def list(self, category=None, start_date=None, end_date=None):
        clauses = []
        params = []
        if category:
            clauses.append('category COLLATE NOCASE = ?')
            params.append(category.strip())
        if start_date:
            clauses.append('spent_on >= ?')
            params.append(self._validate_date(start_date))
        if end_date:
            clauses.append('spent_on <= ?')
            params.append(self._validate_date(end_date))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ''
        query = f'SELECT * FROM expenses{where} ORDER BY spent_on, id'
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params)]

    def total_by_category(self, start_date=None, end_date=None):
        clauses = []
        params = []
        if start_date:
            clauses.append('spent_on >= ?')
            params.append(self._validate_date(start_date))
        if end_date:
            clauses.append('spent_on <= ?')
            params.append(self._validate_date(end_date))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ''
        query = (
            'SELECT category, ROUND(SUM(amount), 2) total, COUNT(*) entry_count '
            f'FROM expenses{where} '
            'GROUP BY category ORDER BY total DESC, category ASC'
        )
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params)]

    def total_by_month(self, start_date=None, end_date=None):
        clauses = []
        params = []
        if start_date:
            clauses.append('spent_on >= ?')
            params.append(self._validate_date(start_date))
        if end_date:
            clauses.append('spent_on <= ?')
            params.append(self._validate_date(end_date))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ''
        query = (
            'SELECT substr(spent_on, 1, 7) month, ROUND(SUM(amount), 2) total, COUNT(*) entry_count '
            f'FROM expenses{where} GROUP BY substr(spent_on, 1, 7) ORDER BY month ASC'
        )
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params)]


def build_parser():
    p = argparse.ArgumentParser(description='Expense tracker')
    p.add_argument('--db', default='expenses.db')
    sub = p.add_subparsers(dest='cmd', required=True)

    a = sub.add_parser('add')
    a.add_argument('category')
    a.add_argument('amount', type=float)
    a.add_argument('--note', default='')
    a.add_argument('--date', dest='spent_on', default=None, help='YYYY-MM-DD')

    l = sub.add_parser('list')
    l.add_argument('--category')
    l.add_argument('--start-date', default=None)
    l.add_argument('--end-date', default=None)

    s = sub.add_parser('summary')
    s.add_argument('--start-date', default=None)
    s.add_argument('--end-date', default=None)
    s.add_argument('--group-by', choices=['category', 'month'], default='category')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    tracker = ExpenseTracker(args.db)
    try:
        if args.cmd == 'add':
            tracker.add(args.category, args.amount, args.note, args.spent_on)
            print('expense added')
        elif args.cmd == 'list':
            rows = tracker.list(args.category, args.start_date, args.end_date)
            for row in rows:
                note_suffix = f" {row['note']}" if row['note'] else ''
                print(f"#{row['id']} {row['spent_on']} {row['category']} ${row['amount']:.2f}{note_suffix}")
        elif args.cmd == 'summary':
            rows = tracker.total_by_month(args.start_date, args.end_date) if args.group_by == 'month' else tracker.total_by_category(args.start_date, args.end_date)
            for row in rows:
                label = row['month'] if args.group_by == 'month' else row['category']
                print(f"{label}: ${row['total']:.2f} ({row['entry_count']} entries)")
    except ValueError as exc:
        raise SystemExit(f'error: {exc}')


if __name__ == '__main__':
    main()
