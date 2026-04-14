# task-tracker-cli

A portfolio-ready command-line task manager with structured metadata, filtering, exports, recurring schedules, and a clean packaged entry point.

## Why it belongs in a CS portfolio
- demonstrates multi-command CLI design with validation and clear error handling
- models persistent task state with priorities, due dates, tags, recurrence rules, and timestamps
- supports filtered querying, sorting, summaries, and portable exports
- shows a realistic workflow feature: completing a recurring task automatically schedules the next occurrence
- ships as a Python package with both direct module execution and an installable `task-tracker` command
- includes automated tests that cover service logic, CLI behavior, and compatibility paths

## Features
- add, update, delete, start, complete, and reopen tasks
- priority levels: `high`, `medium`, `low`
- optional due dates, normalized tags, and recurring schedules (`daily`, `weekly`, `monthly`)
- filter by status, priority, tag, and keyword search
- sort by id, created time, updated time, due date, or priority
- summary metrics for totals, overdue tasks, recurring tasks, and tag coverage
- export filtered task views as CSV or Markdown
- backward-compatible legacy import path via `task_tracker_cli`

## Run locally
```bash
cd projects/task-tracker-cli
./.venv/bin/python -m pytest -q

python3 -m task_tracker --data-file demo/tasks.json add "Build portfolio project" --priority high --due 2026-04-20 --repeat weekly --tag school
python3 -m task_tracker --data-file demo/tasks.json done 1
python3 -m task_tracker --data-file demo/tasks.json list --sort-by due_date
python3 -m task_tracker --data-file demo/tasks.json export --format markdown --output demo/tasks.md
```

## Installable CLI
```bash
cd projects/task-tracker-cli
python3 -m pip install -e .

task-tracker --data-file demo/tasks.json add "Prepare systems demo" --due 2026-04-20 --repeat daily --tag portfolio
```

## Example workflow
```bash
python3 -m task_tracker --data-file demo/tasks.json add "Study graphs" --priority high --tag algorithms
python3 -m task_tracker --data-file demo/tasks.json add "Water plants" --due 2026-04-20 --repeat weekly --tag home
python3 -m task_tracker --data-file demo/tasks.json update 2 --priority medium --tag chores
python3 -m task_tracker --data-file demo/tasks.json done 2
python3 -m task_tracker --data-file demo/tasks.json summary
```

## Test command
```bash
./.venv/bin/python -m pytest -q
```

## Future improvements
- bulk import from CSV or Markdown checklists
- richer terminal UI / ncurses mode
- SQLite-backed storage for multi-user or larger datasets
- configurable reminder/export hooks for calendar sync or notifications
