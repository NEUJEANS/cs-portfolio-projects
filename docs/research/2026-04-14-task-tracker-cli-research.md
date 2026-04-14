# Task Tracker CLI Research

Date: 2026-04-14

## Goal
Build a portfolio-worthy CLI project that shows solid command design, local persistence, input validation, and tests.

## Quick findings
- `argparse` subcommands are the standard Python approach for multi-command CLIs.
- Good student portfolio versions usually include JSON persistence, task status transitions, filtering, sorting, and friendly output/help text.
- Strong versions also validate due dates and priority values instead of accepting arbitrary strings.

## Practical decisions for this repo
- Use **Python 3 stdlib only** to keep local setup simple.
- Use `argparse` subcommands: `add`, `list`, `update`, `start`, `done`, `delete`, `summary`.
- Store tasks in a JSON file with metadata (`created_at`, `updated_at`, `status`, `priority`, `due_date`).
- Add unit tests for storage + service logic and a few CLI integration checks.

## References
- Python argparse docs: https://docs.python.org/3/library/argparse.html
- Real Python argparse guide: https://realpython.com/command-line-interfaces-python-argparse/
- roadmap.sh task tracker project idea: https://roadmap.sh/projects/task-tracker
