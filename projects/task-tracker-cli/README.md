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

## Run
```bash
python3 -m task_tracker_cli --help
python3 -m task_tracker_cli add "Finish systems assignment"
python3 -m task_tracker_cli list --status open
python3 -m task_tracker_cli done 1
python3 -m task_tracker_cli stats
```

By default, data is stored in `.task-tracker/tasks.json` under the current working directory. You can override the path with `TASK_TRACKER_DATA_FILE`.

## Test
```bash
python3 -m unittest discover -s tests -p 'test_task_tracker.py' -v
```

## Next upgrades
- edit task titles
- due dates and priorities
- CSV export
- richer terminal formatting
