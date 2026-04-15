# 2026-04-15 interval-tree benchmark refresh

## Focus
Quick refresh on Python benchmarking and instrumentation patterns for a deterministic CLI lab.

## Notes
- Use `time.perf_counter_ns()` for short benchmark loops to avoid coarse timer granularity.
- Keep workloads reproducible with `random.Random(seed)` instead of the module-global RNG.
- When benchmarking an optimized structure against a baseline, also verify both produce the same outputs during the run.
- Track algorithm-specific work metrics (here: `nodes_visited`) because wall-clock timing alone can be noisy.

## Self-test
1. Why prefer `perf_counter_ns()` here over `time.time()`?
   - It provides a monotonic high-resolution timer better suited for short elapsed-time measurements.
2. Why use a seeded local RNG instead of `random.seed()` globally?
   - It keeps the benchmark reproducible without mutating global random state for tests or future code.
3. Why include node-visit counts in addition to milliseconds?
   - They expose pruning effectiveness even when runtime differences are blurred by interpreter or machine noise.
