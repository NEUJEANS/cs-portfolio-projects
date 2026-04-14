# mini-mapreduce benchmark refresh — 2026-04-14

## Quick refresh
- `time.perf_counter()` is the right lightweight timer for short in-process benchmark comparisons.
- Synthetic fixtures should be deterministic so interview demos and tests do not drift across runs.
- Benchmark output is more useful when it includes both elapsed time and workload-shape metrics like reducer skew.

## Self-test
1. Why prefer `perf_counter()` over `time.time()` here?
   - better monotonic precision for short benchmark windows.
2. Why keep synthetic inputs seed-driven?
   - lets tests verify stable shape/count metrics while still exercising non-trivial workloads.
3. Why log skew alongside timing?
   - reducer imbalance can explain timing differences better than reducer count alone.
