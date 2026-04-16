# 2026-04-16 Karger min-cut benchmark review pass 1

## Focus
CLI safety and benchmark-mode behavior.

## Findings
1. `run` mode failed with an unclear traceback when `--graph-file` was omitted.
2. Benchmark mode itself produced the expected JSON/CSV artifacts and family summaries after the feature landed.

## Fixes
- Added explicit CLI validation so `python3 ... run` exits with `--graph-file is required when command=run`.
- Added a regression test for the missing-graph-file path.
