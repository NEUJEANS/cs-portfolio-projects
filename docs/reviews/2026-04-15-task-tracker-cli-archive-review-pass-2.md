# Task Tracker CLI Archive Review - Pass 2

## Focus
Snapshot reproducibility and archive ordering.

## Checks
- Inspected `archive_completed_tasks` for ordering and storage behavior.
- Reviewed JSON payload shape against expected deterministic outputs for tests and demos.

## Issue found
- Completed tasks were collected in storage order without an explicit sort, which could make archive snapshots less deterministic if the backing file order ever changed.

## Fix applied
- Sorted archived tasks by task id before writing JSON and Markdown snapshots.

## Result
- Archive artifacts are now stable and easier to diff in Git history or compare during demos.
