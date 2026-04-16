# CPU Scheduler Simulator SRTF Review — Pass 2

## Focus
Determinism, tests, and CLI behavior.

## Findings
1. Equal remaining-time cases needed explicit tie-breaking to avoid unstable timelines across runs.
2. The test suite did not yet prove CLI/JSON behavior for the new algorithm.

## Fixes made
- sorted SRTF ready tasks by remaining time, then arrival time, then PID for deterministic execution
- added regression tests for preemption, tie-breaking, and `scheduler.py srtf --json`
