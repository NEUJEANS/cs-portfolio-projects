# deadlock-detector-lab review pass 1

## Focus
Algorithm correctness and CLI smoke run.

## Checks
- ran `python3 -m unittest projects/deadlock-detector-lab/test_deadlock_detector.py`
- ran both sample CLI commands from the README

## Findings
1. Core wait-for graph cycle detection and allocation-state detection behaved as expected on deadlocked and safe fixtures.
2. CLI output was stable and machine-readable.
3. Issue found: invalid JSON/data errors surfaced as raw Python tracebacks instead of clean user-facing CLI errors.

## Fixes made
- wrapped CLI execution in structured exception handling
- added top-level JSON object validation
- added regression tests to ensure clean failure messages
