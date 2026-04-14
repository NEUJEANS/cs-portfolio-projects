# mini-mapreduce-lab review pass 3

## Focus
Repository integration and docs polish.

## Findings
1. Repo-level tests did not include this project under `tests/`, which made the new slice easier to miss from the top-level test workflow.
2. README command examples had collapsed formatting after the edit pass and were harder to scan.

## Fixes applied
- Added `tests/test_mini_mapreduce.py` so the project is covered from the repo-level test suite.
- Restored multiline README command blocks for readability.
