# Task Tracker CLI Review Pass 2

## Checks
- reviewed update-path argument validation and metadata editing behavior
- ran `python3 task_tracker.py --data-file /tmp/task-tracker-slice.json add 'review smoke task' --priority high --due 2026-04-20 --tag demo`
- ran `python3 task_tracker.py --data-file /tmp/task-tracker-slice.json update 1 --clear-due --tag polished`
- ran `python3 task_tracker.py --data-file /tmp/task-tracker-slice.json summary`

## Issues found
1. Clearing a due date was not possible, which made metadata edits feel incomplete.
2. Without an explicit validation guard, users could have passed both `--due` and `--clear-due` in the same update command.

## Fixes applied
- added `--clear-due` support to the maintained CLI
- added a conflict check so `--due` and `--clear-due` cannot be used together
- expanded CLI tests to cover the new behavior

## Result
- task metadata management is more complete and safer to demo from the terminal
