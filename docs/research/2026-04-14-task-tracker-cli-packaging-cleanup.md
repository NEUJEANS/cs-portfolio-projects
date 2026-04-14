# 2026-04-14 Task Tracker CLI Packaging Cleanup Research

## Goal
Strengthen `task-tracker-cli` by removing ambiguity between overlapping implementations and making the packaged command match the maintained code path.

## Brief notes
- No external web research was needed for this slice; the gap was internal repository drift rather than an unfamiliar API or algorithm.
- The most important portfolio fix is consistency: installable entry points, module execution, README commands, and tests should all exercise the same implementation.
- Preserving a thin compatibility namespace is better than keeping multiple divergent copies of business logic.
- A small user-facing feature can ride along with cleanup when it uses the same code path and improves the demo story.

## Slice decision
1. treat `src/task_tracker/` as the maintained implementation
2. convert `src/task_tracker_cli/` into a compatibility wrapper instead of a second codebase
3. point the `task-tracker` script at the maintained package
4. add `--clear-due` so metadata updates are more complete and easier to demo
5. update tests and README so package/install/run paths stay aligned
