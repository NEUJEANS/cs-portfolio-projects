# task-tracker-cli

A small but polished command-line task manager for portfolio use.

## Why it belongs in a CS portfolio
- demonstrates CLI design with subcommands and validation
- persists structured state to disk without external dependencies
- includes filtered views, status transitions, summaries, and automated tests
- leaves room for future upgrades like tags, due dates, or recurring tasks

## Features
- add, rename, delete, and list tasks
- mark tasks as `todo`, `in-progress`, or `done`
- JSON persistence via `--db`
- summary view for quick status counts
- test suite covering happy paths and failure cases

## Run locally
```bash
cd projects/task-tracker-cli
python -m pip install -e .
python -m pytest

task-tracker --db demo.json add "Build portfolio project"
task-tracker --db demo.json mark 1 in-progress
task-tracker --db demo.json list
```

## Example
```bash
task-tracker --db demo.json add "Study graphs"
task-tracker --db demo.json add "Ship CLI"
task-tracker --db demo.json mark 2 done
task-tracker --db demo.json summary
```
