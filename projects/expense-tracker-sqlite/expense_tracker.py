import argparse
import sqlite3
from datetime import date
from pathlib import Path


class ExpenseTracker:
    DEFAULT_ALERT_THRESHOLD = 0.8

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
            conn.execute(
                'CREATE TABLE IF NOT EXISTS budgets ('
                'category TEXT NOT NULL COLLATE NOCASE, '
                'month TEXT NOT NULL, '
                'amount REAL NOT NULL, '
                f'alert_threshold REAL NOT NULL DEFAULT {self.DEFAULT_ALERT_THRESHOLD}, '
                'PRIMARY KEY (category, month)'
                ')'
            )
            budget_columns = {row['name'] for row in conn.execute('PRAGMA table_info(budgets)')}
            if 'alert_threshold' not in budget_columns:
                conn.execute(
                    f'ALTER TABLE budgets ADD COLUMN alert_threshold REAL NOT NULL DEFAULT {self.DEFAULT_ALERT_THRESHOLD}'
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

    def _validate_month(self, month=None):
        if month in (None, ''):
            return date.today().strftime('%Y-%m')
        cleaned = month.strip()
        if len(cleaned) != 7 or cleaned[4] != '-':
            raise ValueError('month must be in YYYY-MM format')
        try:
            date.fromisoformat(f'{cleaned}-01')
        except ValueError as exc:
            raise ValueError('month must be in YYYY-MM format') from exc
        return cleaned

    def _validate_threshold(self, threshold):
        value = float(threshold)
        if value <= 0 or value > 1:
            raise ValueError('alert threshold must be between 0 and 1')
        return round(value, 4)

    def add(self, category, amount, note='', spent_on=None):
        category = self._validate_category(category)
        amount = self._validate_amount(amount)
        spent_on = self._validate_date(spent_on)
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO expenses(category, amount, note, spent_on) VALUES (?, ?, ?, ?)',
                (category, amount, note.strip(), spent_on),
            )

    def set_budget(self, category, amount, month=None, alert_threshold=DEFAULT_ALERT_THRESHOLD):
        category = self._validate_category(category)
        amount = self._validate_amount(amount)
        month = self._validate_month(month)
        alert_threshold = self._validate_threshold(alert_threshold)
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO budgets(category, month, amount, alert_threshold) VALUES (?, ?, ?, ?) '
                'ON CONFLICT(category, month) DO UPDATE SET '
                'amount = excluded.amount, '
                'alert_threshold = excluded.alert_threshold',
                (category, month, amount, alert_threshold),
            )
        return {'category': category, 'month': month, 'amount': amount, 'alert_threshold': alert_threshold}

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

    def list_budgets(self, month=None):
        clauses = []
        params = []
        if month not in (None, ''):
            clauses.append('month = ?')
            params.append(self._validate_month(month))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ''
        query = f'SELECT category, month, amount, alert_threshold FROM budgets{where} ORDER BY month ASC, category ASC'
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

    def budget_status(self, month=None):
        month = self._validate_month(month)
        query = (
            'SELECT '
            'b.category, '
            'b.month, '
            'ROUND(b.amount, 2) budget_amount, '
            'ROUND(COALESCE(SUM(e.amount), 0), 2) spent, '
            'b.alert_threshold '
            'FROM budgets b '
            'LEFT JOIN expenses e '
            'ON b.category = e.category COLLATE NOCASE '
            'AND substr(e.spent_on, 1, 7) = b.month '
            'WHERE b.month = ? '
            'GROUP BY b.category, b.month, b.amount, b.alert_threshold '
            'ORDER BY (COALESCE(SUM(e.amount), 0) / b.amount) DESC, b.category ASC'
        )
        rows = []
        with self._connect() as conn:
            for row in conn.execute(query, (month,)):
                spent = float(row['spent'])
                budget_amount = float(row['budget_amount'])
                remaining = round(budget_amount - spent, 2)
                usage_ratio = spent / budget_amount if budget_amount else 0.0
                status = 'over' if spent > budget_amount else 'warning' if usage_ratio >= float(row['alert_threshold']) else 'ok'
                rows.append({
                    'category': row['category'],
                    'month': row['month'],
                    'budget_amount': budget_amount,
                    'spent': spent,
                    'remaining': remaining,
                    'usage_percent': round(usage_ratio * 100, 1),
                    'alert_threshold': round(float(row['alert_threshold']) * 100, 1),
                    'status': status,
                })
        return rows


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

    budget = sub.add_parser('budget')
    budget_sub = budget.add_subparsers(dest='budget_cmd', required=True)

    budget_set = budget_sub.add_parser('set')
    budget_set.add_argument('category')
    budget_set.add_argument('amount', type=float)
    budget_set.add_argument('--month', default=None, help='YYYY-MM')
    budget_set.add_argument('--threshold', type=float, default=ExpenseTracker.DEFAULT_ALERT_THRESHOLD)

    budget_list = budget_sub.add_parser('list')
    budget_list.add_argument('--month', default=None, help='YYYY-MM')

    budget_status = budget_sub.add_parser('status')
    budget_status.add_argument('--month', default=None, help='YYYY-MM')
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
        elif args.cmd == 'budget':
            if args.budget_cmd == 'set':
                budget = tracker.set_budget(args.category, args.amount, args.month, args.threshold)
                print(
                    f"budget saved for {budget['category']} {budget['month']}: "
                    f"${budget['amount']:.2f} alert at {budget['alert_threshold'] * 100:.1f}%"
                )
            elif args.budget_cmd == 'list':
                rows = tracker.list_budgets(args.month)
                if not rows:
                    month_label = f" for {tracker._validate_month(args.month)}" if args.month else ''
                    print(f'no budgets configured{month_label}')
                for row in rows:
                    print(f"{row['month']} {row['category']}: ${row['amount']:.2f} alert at {row['alert_threshold'] * 100:.1f}%")
            elif args.budget_cmd == 'status':
                month = tracker._validate_month(args.month)
                rows = tracker.budget_status(month)
                if not rows:
                    print(f'no budgets configured for {month}')
                for row in rows:
                    balance = f"over by ${abs(row['remaining']):.2f}" if row['status'] == 'over' else f"${row['remaining']:.2f} remaining"
                    print(
                        f"{row['category']}: ${row['spent']:.2f} / ${row['budget_amount']:.2f} "
                        f"used ({row['usage_percent']:.1f}%) [{row['status']}] {balance}"
                    )
    except ValueError as exc:
        raise SystemExit(f'error: {exc}')


if __name__ == '__main__':
    main()
