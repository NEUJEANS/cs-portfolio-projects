# Task Tracker CLI Review Log

Date: 2026-04-14
Project: `projects/task-tracker-cli`

## Pass 1 - functionality review
Findings:
- Core slice had task CRUD, status transitions, summary output, and JSON persistence.
- Needed an explicit test for invalid due-date updates.

Fixes made:
- Added `test_update_requires_valid_due_date` to cover invalid update input.

## Pass 2 - environment/setup review
Findings:
- CLI smoke tests used `python`, which is not available on this host.
- README examples also used `python`, which would mislead users here.

Fixes made:
- Updated smoke tests to use `python3`.
- Updated README quick-start and test commands to use `python3`.

## Pass 3 - code quality review
Findings:
- Timestamp helper used `datetime.utcnow()`, which is deprecated in modern Python.

Fixes made:
- Replaced it with timezone-aware `datetime.now(UTC)` and normalized the output to `Z` format.

## Final assessment
- Vertical slice is runnable.
- Tests pass locally.
- Repo is ready for secret scan, commit, push, and wrap-up.
