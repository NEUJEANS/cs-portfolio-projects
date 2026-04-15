# Review pass 3 — distributed-snapshot failure/recovery slice

## Focus
Docs/CLI clarity and demo readiness.

## Checks
- README examples now cover outage capture and script playback
- Mermaid rendering includes FAIL/RECOVER notes and process-status summaries
- CLI surface stays small: `simulate`, `concurrent`, and `script`
- tests cover parser validation, failure blocking, recovery, script snapshots, Mermaid output, and existing concurrent behavior

## Result
No further code changes needed after the final targeted test run and smoke check.
