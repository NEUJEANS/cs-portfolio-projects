# Learning Refresh — 2026-04-15 — Suffix Tree Benchmark Self-Test

## Refresh points
- Overlapping substring matches cannot rely on a naive regex without lookahead.
- A plain `str.find` loop can capture overlapping hits by restarting at `index + 1`.
- Benchmark output is more trustworthy when correctness is validated before timings are recorded.

## Quick self-test
1. Why not use `re.findall(pattern)` here?
   - Because it would skip overlapping matches for patterns like `ana` in `banana`.
2. Why cross-check benchmark counts between all methods?
   - To avoid publishing timings for methods that accidentally implement different semantics.
3. Why export CSV instead of only printing a table?
   - CSV is easy to diff, commit, graph later, and reuse in artifacts or notebooks.

## Slice rule
Prefer small benchmark surfaces that are correct, reproducible, and artifact-friendly over a more ambitious but under-tested performance harness.
