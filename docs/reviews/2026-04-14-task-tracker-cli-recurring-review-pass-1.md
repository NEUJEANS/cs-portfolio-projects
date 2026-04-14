# 2026-04-14 task-tracker-cli recurring review — pass 1

## Focus
Domain model and scheduling behavior.

## Issue found
- Clearing a recurrence rule from the CLI initially passed `None`, which was indistinguishable from "leave recurrence unchanged" in the service layer.

## Fix applied
- Changed CLI update handling so `--clear-repeat` sends an explicit empty value that normalizes to `None`, allowing recurrence to be removed intentionally.

## Result
- Recurrence can now be added, replaced, and cleared through one consistent service path.
