# Expense tracker SQLite recurring budget template review — 2026-04-19

## Pass 1 — seeding contract audit
- Reviewed the new template-seeding flow for resumability and argument correctness.
- Issue found: `source_month` / `--from-month` could be supplied even when rollover was disabled, which made the argument silently useless and easy to misunderstand.
- Fix applied: `seed_budget_month(...)` now rejects `source_month` unless rollover seeding is enabled, and the previous month is only derived when rollover is actually requested.
- Validation: `test_seed_budget_month_rejects_source_month_without_rollover` and `test_cli_returns_clean_error_for_invalid_input`.

## Pass 2 — ordering and migration audit
- Reviewed stable output ordering and schema initialization for older databases.
- Issue found: template/budget listings were ordered with default text collation, which can produce awkward case-sensitive ordering in generated examples and screenshots.
- Fix applied: switched listing queries to `COLLATE NOCASE` ordering and added migration coverage for legacy `budget_templates` tables missing `alert_threshold`.
- Validation: `test_budget_template_upsert_and_list`, `test_migrates_existing_budget_template_table_without_alert_threshold`, and `test_seed_budget_month_skips_existing_unless_replace_requested`.

## Pass 3 — CLI/docs smoke audit
- Reviewed the README usage examples, empty-state behavior, and real CLI flow for template creation plus seeded month generation.
- Issue found: the project docs still described templates as a future idea rather than a first-class command flow.
- Fix applied: updated the README feature/usage sections for `budget template set|list` and `budget seed`, then reran the focused suite plus a manual temp-DB smoke flow.
- Validation: `./.venv/bin/python -m pytest -q projects/expense-tracker-sqlite/test_expense_tracker.py`, `./.venv/bin/python -m py_compile projects/expense-tracker-sqlite/expense_tracker.py projects/expense-tracker-sqlite/test_expense_tracker.py`, and manual `budget template` / `budget seed` commands against a temp SQLite database.
