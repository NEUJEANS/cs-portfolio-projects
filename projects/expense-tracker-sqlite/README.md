# expense-tracker-sqlite

## Overview
Record expenses in SQLite, filter entries by date/category, and generate category or month-level spending summaries.

## Why it is portfolio-worthy
- demonstrates SQLite schema management and lightweight migrations
- shows practical CLI design with filtered queries and reporting modes
- covers validation, persistence, analytics, and automated tests in one small project

## Stack
- Python 3
- SQLite via the standard library
- unittest for automated test coverage

## Features
- add expenses with category, amount, note, and explicit purchase date
- list expenses with category and date-range filters
- summarize totals by category for a selected window
- summarize totals by month for trend reporting
- set per-category monthly budgets with configurable threshold alerts
- report budget status with warning/over-budget states and remaining balance
- migrate older databases missing the `spent_on` column
- validate positive amounts, ISO dates, and `YYYY-MM` budget months

## Usage
```bash
python3 expense_tracker.py --db expenses.db add food 12.50 --note lunch --date 2026-04-10
python3 expense_tracker.py --db expenses.db list --category food --start-date 2026-04-01 --end-date 2026-04-30
python3 expense_tracker.py --db expenses.db summary
python3 expense_tracker.py --db expenses.db summary --group-by month
python3 expense_tracker.py --db expenses.db budget set food 200 --month 2026-04 --threshold 0.8
python3 expense_tracker.py --db expenses.db budget status --month 2026-04
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- add recurring month-to-month budget templates and rollover support
- export filtered reports to CSV or Markdown
- support merchant-level aggregation and richer dashboards
