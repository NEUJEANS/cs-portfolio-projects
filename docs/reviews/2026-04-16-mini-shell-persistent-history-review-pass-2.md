# Mini Shell Persistent History Review — Pass 2

## Findings
1. The README explained the REPL history file but did not clearly say that direct `run_command()` callers must pass `history_path` to get the same persistence behavior.
2. That gap made the feature easier to misunderstand when reading the project code and tests side by side.

## Fixes applied
- clarified the README usage section so the REPL default and the `run_command(history_path=...)` testing/programmatic path are both explicit

## Result
The docs now match the implementation boundary: persistence is automatic in the REPL and opt-in for direct function calls.
