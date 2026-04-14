# Task Tracker CLI Review Log — 2026-04-14

## Pass 1 — repository state and runnable path
- Issue found: the repo contained multiple overlapping task tracker implementations (`task_tracker.py`, `src/task_tracker.py`, `src/task_tracker/`, `src/task_tracker_cli/`), which made the runnable entry point ambiguous.
- Fix applied: chose `src/task_tracker/` as the maintained implementation and changed the root `task_tracker.py` to a thin wrapper that forwards to the package entry point.

## Pass 2 — CLI/test compatibility
- Issue found: CLI smoke tests expected package exports (`TaskService`, `TaskStorage`, `TaskTrackerError`) that were missing from `src/task_tracker/__init__.py`.
- Fix applied: re-exported the task domain/service/storage API and aligned the packaged CLI with the tested subcommands and output patterns.

## Pass 3 — test reliability and UX polish
- Issue found: new CLI tests were invoking `python -m task_tracker`, but the older root script shadowed the package module; one test also expected the wrong validation text.
- Fix applied: updated the wrapper entry point, preserved the system environment while adding `PYTHONPATH`, corrected test expectations, and reran the full suite until green.

## Outcome
- Final result: 11/11 tests passing.
- Remaining follow-up: remove or fully migrate the older duplicate source trees (`src/task_tracker.py` and `src/task_tracker_cli/`) in a future cleanup slice.
