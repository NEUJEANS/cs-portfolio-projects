# Chord DHT hop benchmark refresh and self-test — 2026-04-15

## Refresh points
- A baseline benchmark is strongest when it changes only one major variable; here that variable is routing strategy.
- Linear successor forwarding is a clean control because it preserves the same owner-selection logic as Chord.
- Benchmark summaries should include both aggregate numbers and per-case traces so results stay explainable.
- Deduplicating requested start nodes avoids accidental double-counting in benchmark summaries.

## Self-test
1. If two lookup strategies disagree on the owner for the same key in the same ring, the benchmark is invalid.
2. If the same start node is passed twice, the benchmark should not silently duplicate those cases.
3. Average hops can tie on some small workloads even when the optimized strategy is still correct and beneficial on harder cases.

## Implementation reminders
- keep route ordering deterministic for tests and review logs
- validate any optional benchmark start nodes against the loaded ring
- round aggregate hop averages so CLI JSON stays readable without losing the trend
