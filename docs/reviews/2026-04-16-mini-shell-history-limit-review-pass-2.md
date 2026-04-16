# Mini Shell History Limit Review — Pass 2

## Findings
1. `get_repl_history_limit()` rejected negative values, but there was no matching regression test for a non-numeric environment value such as `MINI_SHELL_HISTORY_LIMIT=many`.
2. That left the environment-parsing boundary under-specified even though it is part of the new user-facing configuration surface.

## Fixes applied
- added a unit test that asserts non-numeric `MINI_SHELL_HISTORY_LIMIT` values raise the same clear validation error as negative values

## Result
The REPL configuration path is now pinned for both numeric-range errors and plain parsing errors.
