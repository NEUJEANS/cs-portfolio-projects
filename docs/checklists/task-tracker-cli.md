# Task Tracker CLI Checklist

## Goal
Build a portfolio-friendly command-line task manager that demonstrates:
- argument parsing
- persistent storage
- filtering and reporting
- testable domain logic
- clean project structure and docs

## Vertical slice status
- [x] Create project scaffolding
- [x] Implement persistent task store using JSON
- [x] Implement `add` command
- [x] Implement `list` command with filters
- [x] Implement `done` command
- [x] Implement `delete` command
- [x] Implement `stats` command
- [x] Add readable CLI help text
- [x] Add unit tests for repository + service + CLI output
- [x] Add usage-focused project README
- [x] Add task editing / renaming
- [x] Add due dates / priorities
- [x] Add import/export support
- [x] Add completed-task archive snapshots
- [x] Add richer terminal formatting

## Current archive slice
- [x] Add `archive` command with default archive directory near the data store
- [x] Write timestamped JSON and Markdown archive snapshots
- [x] Prune completed tasks from the active store by default
- [x] Support `--keep` mode for non-destructive archiving
- [x] Cover archive flows with service + CLI tests
- [x] Refresh README usage examples for the archive workflow

## Current restore slice
- [x] Add `restore` command for replaying JSON archive snapshots back into the active store
- [x] Preserve archive immutability by assigning fresh ids to restored tasks
- [x] Support optional `--status` override for replaying old work as a new todo queue
- [x] Cover restore flows with service + CLI tests
- [x] Refresh README usage examples for archive recovery

## Notes for next run
- Bulk actions would make repeated demo workflows stronger.
- A future slice could add saved views or dashboard-style reporting on top of the richer terminal formatting.
