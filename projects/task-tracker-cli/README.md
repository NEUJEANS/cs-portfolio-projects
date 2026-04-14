# Task Tracker CLI

A small but polished command-line task tracker built with Python's standard library.

## Why it belongs in a CS portfolio
- demonstrates CLI design with `argparse`
- shows persistent local storage with atomic JSON writes
- separates data model, business logic, and presentation
- includes automated tests for core flows

## Features
- add tasks
- list all, open-only, or completed tasks
- mark tasks done
- delete tasks
- print summary statistics
- import tasks from CSV or JSON snapshots
- export filtered task views as CSV or Markdown

## Run
```bash
python3 -m src.task_tracker --help
python3 -m src.task_tracker add "Finish systems assignment"
python3 -m src.task_tracker list --status todo
python3 -m src.task_tracker done 1
python3 -m src.task_tracker summary
python3 -m src.task_tracker export --format csv --output tasks.csv
python3 -m src.task_tracker import sample_tasks.json --format json
```

By default, data is stored in `data/tasks.json` under the current working directory. You can override the path with `--data-file`.

## Test
```bash
.venv/bin/pytest tests -q
```

## Next upgrades
- richer terminal formatting
- bulk task actions (complete/delete by filter)
- archive completed tasks into dated snapshots
