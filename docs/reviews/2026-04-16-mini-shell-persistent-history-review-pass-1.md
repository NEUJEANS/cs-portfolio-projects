# Mini Shell Persistent History Review — Pass 1

## Findings
1. The new persistent-history slice depended on `MINI_SHELL_HISTORY_FILE`, but there was no regression test proving that an empty value really disables file-backed history in the REPL helper.
2. Without that test, a future refactor could silently re-enable persistence for users who explicitly turned it off.

## Fixes applied
- added a focused unit test for `get_repl_history_path()` with `MINI_SHELL_HISTORY_FILE=""`
- kept the environment override isolated and restored after the test to avoid cross-test leakage

## Result
The environment-based “disable persistent history” path is now pinned by an automated test.
