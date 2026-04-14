# task-tracker-cli

A polished Python command-line task tracker that demonstrates practical CS portfolio skills: CLI design, persistence, validation, sorting, and test coverage.

## Why this project matters
- demonstrates command-line UX with multiple subcommands
- shows JSON-backed persistence and data modeling
- includes validation for status, priority, and due dates
- supports automated tests and review-driven iteration
- leaves a clear extension path for packaging, tags, and exports

## Features
- add tasks with description, priority, and optional due date
- list tasks with filtering and sorting
- update task fields after creation
- move tasks into `in-progress`, `done`, or back to `todo`
- print a summary report for portfolio demos
- delete tasks cleanly
- persist tasks to a local JSON file

## Quick start
```bash
python3 -m task_tracker --help
python3 -m task_tracker --db tasks.json add "Ship portfolio MVP" --priority high --due 2026-04-20
python3 -m task_tracker --db tasks.json list --sort-by priority
python3 -m task_tracker --db tasks.json start 1
python3 -m task_tracker --db tasks.json done 1
python3 -m task_tracker --db tasks.json summary
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
- tags and text search
- colored terminal output
- CSV or Markdown export
- packaging for `pipx` installation
