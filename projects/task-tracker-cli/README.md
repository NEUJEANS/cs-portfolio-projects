# Task Tracker CLI

A portfolio-friendly command-line task manager built with Python and JSON persistence.

## Features
- add tasks with priority and due dates
- list tasks with status/priority search filters
- mark tasks as done
- delete tasks
- show summary statistics
- print either table-style text or JSON
- persist data safely with atomic writes

## Run
```bash
python3 -m src.task_tracker_cli --help
python3 -m src.task_tracker_cli add "Finish OS assignment" --priority high --due 2026-04-20
python3 -m src.task_tracker_cli list --status todo
python3 -m src.task_tracker_cli done 1
python3 -m src.task_tracker_cli summary
```

## Optional custom data file
```bash
python3 -m src.task_tracker_cli --db /tmp/tasks.json add "Test task"
```

## Tests
```bash
python3 -m unittest discover -s tests -v
```
