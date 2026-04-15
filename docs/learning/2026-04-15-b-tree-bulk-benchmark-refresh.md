# B-tree bulk-load benchmark refresh — 2026-04-15

## Quick refresh
- `time.perf_counter_ns()` is a good standard-library timer for short benchmark intervals.
- Repeated runs are needed because tiny build workloads are noisy.
- Benchmark helpers should validate comparable outputs before claiming a speedup.

## Self-test
1. Why compare identical sorted outputs before reporting timings?
   - To ensure the faster path is not accidentally skipping work or building a different tree.
2. Why use repeated runs instead of one measurement?
   - Short-running Python code is sensitive to timing noise from interpreter/runtime effects.
3. Why keep this benchmark inside the CLI?
   - It makes the feature easy to demo, rerun, and discuss in interviews.
