# Task Tracker CLI Research

## Why this project
A task tracker is a strong first portfolio project because it shows command-line UX, CRUD flows, persistence, validation, testing, and clean program structure without requiring a heavy framework.

## Brief notes from research
- Useful baseline features: add/list/update/delete, status transitions, priorities, due dates, filtering, timestamps, and machine-readable output.
- Good CLI practice: predictable subcommands, clear errors, helpful `--help`, and JSON output for scripting.
- Simple local persistence is enough for an entry portfolio slice when wrapped with validation and tests.

## Design choices for this slice
- Language: Python 3.14 with `argparse` and `dataclasses`
- Storage: JSON file persisted atomically
- Focus: a polished vertical slice instead of a huge unfinished app
- Included now: add, list, done, delete, summary, filters, priority, due dates, JSON output
- Later upgrades: edit command, tags, bulk import/export, TUI mode

## References
- https://cobra.dev/docs/examples/02-task-manager/
- https://simonwillison.net/2023/Sep/30/cli-tools-python/
- https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis
