# Review pass 2 — B-tree bulk benchmark

## Focus
- invariant and correctness audit
- benchmark methodology sanity check

## Findings
- Benchmark helper now rejects unsorted or duplicate-key inputs instead of silently producing misleading comparisons.
- The helper verifies generic-insert and bulk-load outputs match before reporting timings.
- Timing is intentionally lightweight and should be treated as relative guidance, not a stable cross-machine metric.

## Fixes made
- enforced `repeats >= 1`
- preserved identical stats output for both build paths in the benchmark summary
