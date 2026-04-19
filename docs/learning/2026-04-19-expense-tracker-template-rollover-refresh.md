# 2026-04-19 expense tracker template + rollover refresh

## Quick refresher
- Recurring monthly budgets fit cleanly as a separate `budget_templates` table instead of overloading month-specific `budgets`; that keeps seeding idempotent and the monthly status query simple.
- For resumable automation, seeding should skip existing month/category budgets by default and only overwrite when explicitly requested.
- Positive-only rollover is a good first slice: it demonstrates carry-forward logic without forcing the whole tracker to support zero or negative seeded budgets.
- `--from-month` should not silently do nothing; if rollover is disabled, reject the argument so the CLI contract stays trustworthy.

## Self-test commands
```bash
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-template-demo.db budget template set food 200 --threshold 0.8
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-template-demo.db budget template set rent 900 --threshold 0.9
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-template-demo.db budget set food 100 --month 2026-04 --threshold 0.8
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-template-demo.db add food 60 --date 2026-04-11
./.venv/bin/python projects/expense-tracker-sqlite/expense_tracker.py --db /tmp/expense-template-demo.db budget seed 2026-05 --rollover --from-month 2026-04
```

## What to remember next run
- The tracker now supports recurring budget templates and positive remaining-balance rollover seeding.
- The next natural slice is exportable budget artifacts: CSV/Markdown month reports or portfolio-ready dashboard snapshots built from `budget list/status` output.
