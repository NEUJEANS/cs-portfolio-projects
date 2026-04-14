# 2026-04-14 Task Tracker CLI Tags/Search Review - Pass 1

Focus: code-path audit for the new tags/search slice.

## Checks
- read `src/task_tracker/store.py` and `src/task_tracker/cli.py`
- traced add/list/update flows for new tag metadata
- verified backward compatibility for old task JSON by defaulting missing `tags` to `[]`

## Issue found
- `update` accepted both `--tag` and `--clear-tags` together, which created ambiguous intent.

## Fix applied
- added an explicit CLI validation error: `Use either --tag or --clear-tags, not both.`
- added a regression test for the conflicting-flag case
