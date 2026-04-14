# Python CLI refresh + self-test

Date: 2026-04-14
Project: task-tracker-cli

## Refresher focus
- `argparse` subparsers for multi-command CLIs
- `dataclass` for structured task records
- simple JSON file persistence via `pathlib`
- pytest fixtures with temporary directories

## Quick self-test
1. How do you share a global `--db` option across subcommands?
   - add it on the top-level parser before creating subparsers
2. What is the simplest durable storage choice for a first CLI slice?
   - a JSON file with explicit schema and tests
3. How do you keep tests isolated from user state?
   - use pytest `tmp_path` and pass `--db` explicitly
4. When should the CLI exit non-zero?
   - on invalid operations like referencing a missing task
