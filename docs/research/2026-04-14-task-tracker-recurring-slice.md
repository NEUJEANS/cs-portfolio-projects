# 2026-04-14 Task Tracker CLI Recurring Tasks Research

## Goal
Make `task-tracker-cli` feel less like a toy CRUD demo by adding a workflow users actually revisit over time.

## Brief notes
- Recurring tasks are a strong next slice because they touch data modeling, command UX, date arithmetic, and tests without requiring a framework change.
- A lightweight recurrence model (`daily`, `weekly`, `monthly`) is enough for a portfolio project; full RFC recurrence rules would add complexity faster than value.
- The cleanest CLI behavior is to keep the existing `done` command and automatically create the next occurrence when a recurring task is completed.
- Monthly recurrence should clamp to the last valid day in shorter months so dates like January 31 stay usable.

## Slice decision
- add a `recurrence` field to the task model
- support `--repeat` on `add` and `update`
- support `--clear-repeat` on `update`
- require a due date for recurring tasks
- make `done` auto-spawn the next recurring task with copied metadata and an advanced due date
- surface recurrence in list output, summary data, and exports
