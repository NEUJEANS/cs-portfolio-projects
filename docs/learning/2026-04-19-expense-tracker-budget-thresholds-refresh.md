# 2026-04-19 expense tracker budget thresholds refresh

## Quick refresher
- Monthly budget tracking is strongest when it stays category-scoped and month-scoped first; rollover logic can come later.
- SQLite can do a clean budget upsert with `PRIMARY KEY (category, month)` plus `COLLATE NOCASE` on `category`, which keeps category matching case-insensitive without forcing lowercased display text everywhere.
- A small CLI should validate `YYYY-MM` explicitly instead of accepting loose partial dates, otherwise status/report commands become hard to trust.
- Threshold alerts should distinguish between “warning” (crossed configured threshold) and “over” (spent more than budget), because those are different student-demo stories.

## Self-test commands
```bash
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-budget-demo.db add Food 40 --date 2026-04-05
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-budget-demo.db add food 50 --date 2026-04-17
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-budget-demo.db budget set food 100 --month 2026-04 --threshold 0.8
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-budget-demo.db budget status --month 2026-04
```

## What to remember next run
- The current slice covers monthly budget storage and reporting, not recurring templates or rollover budgets.
- The next natural extension is budget templates that auto-seed a new month, then export those status reports as CSV/Markdown artifacts for portfolio screenshots.
