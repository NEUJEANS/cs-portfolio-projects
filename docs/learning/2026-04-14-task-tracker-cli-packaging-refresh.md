# 2026-04-14 Task Tracker CLI Packaging Refresh

## Short refresh
- `python -m package_name` executes `package_name/__main__.py`, so the module entry path should stay wired to the same maintained CLI function as the console script.
- Python package console scripts in `pyproject.toml` should point at the canonical implementation, not a stale compatibility module.
- Thin compatibility shims are fine when they only re-export symbols and delegate behavior.

## Self-check
- If `task-tracker` installs from `task_tracker.cli:main`, should `python -m task_tracker` use a different command parser?
  - No. They should both reach the same CLI implementation so docs/tests do not drift.
- If an older namespace is still imported by tests or users, should it duplicate logic?
  - No. A wrapper layer is safer and easier to maintain.
