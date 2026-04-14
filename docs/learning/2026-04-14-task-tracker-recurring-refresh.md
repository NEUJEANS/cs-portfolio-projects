# 2026-04-14 Task Tracker CLI Recurring Refresh

## Quick refresh
- `datetime.timedelta(days=7)` is enough for daily/weekly recurrence, but monthly schedules need explicit calendar handling.
- `calendar.monthrange(year, month)` is a simple stdlib way to clamp a carried day to the last valid day of the target month.
- Recurrence validation belongs in the domain layer so CLI flags and direct service calls cannot drift.

## Self-test
1. What should happen if a recurring task has no due date?
   - Reject it, because the next occurrence cannot be scheduled deterministically.
2. How should a monthly task due on January 31 advance?
   - To February 28 (or 29 in leap years), not an invalid date.
3. Why spawn the next occurrence on completion instead of pre-creating all future tasks?
   - It keeps the dataset small, matches user intent, and avoids cluttering the CLI.
