# Mini Shell History Limit Review — Pass 3

## Findings
1. The new history-cap logic validated limits internally, but there was no direct regression test proving that a caller cannot pass `history_limit=-1` into `run_command()`.
2. Without that test, a future refactor could accidentally weaken validation for programmatic callers while the REPL path stayed covered.

## Fixes applied
- added a focused unit test that verifies direct `run_command(..., history_limit=-1)` calls fail with the expected validation message

## Result
Both the REPL environment path and the direct function-call path now enforce the same non-negative history-limit contract.
