# Review Pass 2 — memory-allocator-simulator

## Focus
CLI/docs alignment and smoke-test behavior.

## Findings
1. The README test command used `pytest`, but this repo environment does not guarantee pytest.
2. CLI output needed a real smoke check after compaction to confirm layout ordering.

## Fixes applied
- update README to use `python3 -m unittest ...`
- run a CLI smoke test covering allocate/free/compact flow and verify resulting layout in JSON

## Result
The documented test command now matches the runnable environment and the CLI flow was validated end-to-end.
