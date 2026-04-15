# Task Tracker CLI

A polished command-line task tracker built with Python's standard library, with enough workflow depth to feel like a real daily-driver utility instead of a toy CRUD demo.

## Why it belongs in a CS portfolio
- demonstrates CLI design with `argparse`
- shows persistent local storage with atomic JSON writes
- models task metadata like priority, due dates, tags, and recurrence
- supports import/export and archive flows for lifecycle management
- separates data model, business logic, and presentation with automated tests

## Features
- add tasks with priority, due date, tags, and recurrence rules
- list tasks with filters, search, sorting, table output, or JSON output
- emphasize statuses, priorities, and urgent due dates in terminal-friendly task tables with optional ANSI colors
- update fields without rewriting the full task
- mark tasks in progress, done, or reopened
- apply bulk actions to filtered task slices for inbox cleanup and weekly review workflows
- automatically spawn the next task instance for recurring work
- import tasks from CSV or JSON snapshots
- export filtered task views as CSV or Markdown
- archive completed tasks into dated JSON + Markdown snapshots
- restore archived tasks back into the active store with new ids when needed
- print summary statistics including overdue, tagged, and recurring counts with a richer human-readable dashboard view

## Run
```bash
python3 -m src.task_tracker --help
python3 -m src.task_tracker add "Finish systems assignment" --priority high --due 2026-04-20 --tag school --tag systems
python3 -m src.task_tracker list --status todo --sort-by due_date
python3 -m src.task_tracker --color always summary
python3 -m src.task_tracker start 1
python3 -m src.task_tracker done 1
python3 -m src.task_tracker bulk done --tag school --status todo
python3 -m src.task_tracker archive
python3 -m src.task_tracker restore data/archives/completed-2026-04-15T21-30-00Z.json --status todo
python3 -m src.task_tracker export --format markdown --output tasks.md
python3 -m src.task_tracker import sample_tasks.json --format json
```

By default, data is stored in `data/tasks.json` under the current working directory. You can override the path with `--data-file`.

## Archive workflow
Archiving writes dated snapshots under `data/archives/` by default:

```bash
python3 -m src.task_tracker archive
python3 -m src.task_tracker archive --output-dir backups/task-archives
python3 -m src.task_tracker archive --keep
```

Each archive run creates:
- a JSON snapshot with archive metadata and the completed tasks
- a Markdown snapshot that is easy to inspect in GitHub or attach to project notes

Without `--keep`, archived completed tasks are removed from the active task store so the remaining list stays focused.

## Restore workflow
If you want to bring archived tasks back into the active store, replay a JSON snapshot:

```bash
python3 -m src.task_tracker restore data/archives/completed-2026-04-15T21-30-00Z.json
python3 -m src.task_tracker restore data/archives/completed-2026-04-15T21-30-00Z.json --status todo
```

Restored tasks are appended with fresh ids so older snapshots stay immutable and replayable. Use `--status todo` when you want an archive to become a fresh working queue instead of staying marked done.

## Test
```bash
python3 -m pytest tests -q
```

## Implementation notes
- keeps parsing, validation, persistence, and CLI rendering separate so tests can hit each layer cleanly
- normalizes tags and validates recurrence/due-date relationships before data is saved
- archives use timestamped filenames to make repeated snapshots resumable and conflict-free
- keeps human-friendly ANSI styling optional so JSON/export flows stay automation-safe

## Next upgrades
- saved views or dashboard presets for common task slices
- optional archive restore command for replaying old completed work into the active store
- richer bulk archive flows that can snapshot a filtered subset before pruning it
