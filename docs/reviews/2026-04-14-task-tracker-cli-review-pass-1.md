# Task Tracker CLI Review Pass 1

## Checks
- reviewed package layout, entry points, and README commands
- ran `./.venv/bin/python -m pytest -q`

## Issues found
1. The new tests initially imported `task_tracker.cli`, but the root `task_tracker.py` wrapper shadows the package name when running from the project directory.
2. The compatibility namespace still pointed at a duplicate implementation instead of the maintained package.

## Fixes applied
- updated tests to target `src.task_tracker`, which is the maintained in-repo source path
- rewired `src/task_tracker_cli/` into a thin forwarding layer over `src.task_tracker`

## Result
- the repo now has one maintained implementation path and one compatibility shim instead of two divergent CLIs
