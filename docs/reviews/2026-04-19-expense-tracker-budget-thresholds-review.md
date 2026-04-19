# Expense tracker SQLite budget threshold review — 2026-04-19

## Pass 1 — data-model and category-matching audit
- Reviewed the new budget storage and status query end to end.
- Issue found: budget rows must match expense categories case-insensitively or mixed-case expense history (`Food` vs `food`) will undercount budget usage.
- Fix applied: stored budget categories with `COLLATE NOCASE`, used a case-insensitive join in `budget_status(...)`, and added regression coverage for mixed-case expense categories.
- Validation: `test_budget_status_reports_warning_and_overages_case_insensitively`.

## Pass 2 — migration and validation audit
- Reviewed schema initialization for resumability on older databases.
- Issue found: the new `alert_threshold` column introduced a legacy-migration path that was not locked down by tests, and loose month handling would make budget reports unreliable.
- Fix applied: added explicit `YYYY-MM` validation via `_validate_month(...)` and added a regression test for migrating a pre-threshold `budgets` table.
- Validation: `test_budget_upsert_and_validation` and `test_migrates_existing_budget_table_without_alert_threshold`.

## Pass 3 — CLI/docs smoke audit
- Reviewed README usage, empty-state messaging, and the budget CLI output after the schema changes.
- Issue found: the empty budget-list message read awkwardly when no month was specified.
- Fix applied: tightened the empty-state copy to `no budgets configured` or `no budgets configured for YYYY-MM`, then reran the project-local test suite and a manual CLI smoke flow.
- Validation: `./.venv/bin/python -m pytest -q projects/expense-tracker-sqlite/test_expense_tracker.py`, `git diff --check`, and manual `budget set/list/status` commands against a temp SQLite database.
