# Task Tracker CLI Review Log - 2026-04-14

## Review pass 1 - correctness
Issue found: new tasks called `now_iso()` twice, which could produce slightly different `created_at` and `updated_at` values on creation.
Fix: generate one timestamp and reuse it for both fields.

## Review pass 2 - maintainability
Issue found: JSON listing used a brittle manual dataclass-field extraction expression.
Fix: switched to `dataclasses.asdict()` for clearer serialization.

## Review pass 3 - UX and edge cases
Issue found: title validation existed, but it was not covered by tests; not-found command behavior also needed coverage.
Fix: added tests for empty titles and missing task IDs.
