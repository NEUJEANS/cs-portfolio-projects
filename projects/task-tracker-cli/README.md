# task-tracker-cli

A polished Python command-line task tracker that demonstrates practical CS portfolio skills: CLI design, persistence, validation, sorting, metadata modeling, and test coverage.

## Why this project matters
- demonstrates command-line UX with multiple subcommands
- shows JSON-backed persistence and data modeling
- includes validation for status, priority, due dates, and tag metadata
- supports automated tests and review-driven iteration
- leaves a clear extension path for packaging, exports, and richer terminal UX

## Features
- add tasks with description, priority, optional due date, and repeatable tags
- list tasks with filtering by status, priority, keyword search, and required tags
- update task fields after creation, including replacing or clearing tags
- move tasks into `in-progress`, `done`, or back to `todo`
- print a summary report with overdue and tag coverage metrics
- delete tasks cleanly
- persist tasks to a local JSON file

## Quick start
```bash
python3 -m task_tracker --help
python3 -m task_tracker --db tasks.json add "Ship portfolio MVP" --priority high --due 2026-04-20 --tag school --tag demo
python3 -m task_tracker --db tasks.json list --sort-by priority --tag demo
python3 -m task_tracker --db tasks.json list --search portfolio --json
python3 -m task_tracker --db tasks.json update 1 --tag school --tag backend
python3 -m task_tracker --db tasks.json start 1
python3 -m task_tracker --db tasks.json done 1
python3 -m task_tracker --db tasks.json summary --json
```

## Development
```bash
python3 -m unittest discover -s tests -v
```

## Project structure
- `src/task_tracker/` - packaged implementation used by tests and CLI entry points
- `tests/` - unit and CLI smoke tests
- `data/` - local JSON storage when running with the default path

## Next extensions
- colored terminal output
- CSV or Markdown export
- packaging for `pipx` installation
- recurring tasks or reminders
