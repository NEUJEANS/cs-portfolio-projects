# Task Tracker CLI

A Python command-line app for managing personal tasks with JSON persistence, due dates, priorities, status tracking, and summary output.

## Features
- add tasks with optional due dates and priorities
- list tasks with status/priority filters and sort order
- update task fields safely
- move tasks through `todo -> in-progress -> done`
- delete tasks by ID
- print a quick summary of task counts by status
- store data in a local JSON file
- stdlib-only implementation

## Quick start
```bash
python3 -m src.task_tracker --data-file ./data/tasks.json add "Finish portfolio project" --priority high --due 2026-04-20
python3 -m src.task_tracker --data-file ./data/tasks.json list --sort-by due_date
python3 -m src.task_tracker --data-file ./data/tasks.json start 1
python3 -m src.task_tracker --data-file ./data/tasks.json done 1
python3 -m src.task_tracker --data-file ./data/tasks.json summary
```

## Commands
- `add DESCRIPTION [--priority low|medium|high] [--due YYYY-MM-DD]`
- `list [--status todo|in-progress|done] [--priority low|medium|high] [--sort-by created_at|updated_at|due_date|priority|id]`
- `update ID [--description TEXT] [--priority ...] [--due YYYY-MM-DD] [--status ...]`
- `start ID`
- `done ID`
- `delete ID`
- `summary`

## Testing
```bash
python3 -m unittest discover -s tests -v
```
