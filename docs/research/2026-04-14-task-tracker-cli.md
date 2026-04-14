# Research note: task-tracker-cli

Date: 2026-04-14

## Why start here
A task tracker is a strong first portfolio slice because it is small enough to finish cleanly but rich enough to demonstrate:
- CLI UX and command design
- persistence and data modeling
- validation and error handling
- test discipline
- room for future extension

## Portfolio quality targets
- avoid toy-only code by supporting multiple commands and persistent state
- keep setup friction low so recruiters can run it quickly
- include tests and a short README with example usage
- prefer clean architecture over premature complexity

## Scope for this slice
- Python CLI with argparse
- JSON persistence with explicit `--db` path
- add/update/delete/list/mark/summary commands
- automated tests for main workflows and invalid task IDs

## Next likely upgrades
- tags, due dates, priorities
- sorting and search
- CSV export
- richer TUI or SQLite-backed version
