# Task Tracker CLI Archive Review - Pass 3

## Focus
CLI guardrails and parser coverage.

## Checks
- Reviewed CLI command wiring and pytest coverage after the archive feature landed.
- Verified error-path behavior for `archive` when no completed tasks exist.

## Issue found
- The archive command path lacked direct parser coverage and an explicit regression test for the no-completed-tasks failure case.

## Fix applied
- Added pytest coverage for `archive --keep --output-dir ...` parsing and for the user-facing error when archiving without completed tasks.

## Result
- Archive command behavior is covered on both success and failure paths.
