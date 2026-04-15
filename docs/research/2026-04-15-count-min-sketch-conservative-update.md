# Count-Min Sketch conservative update notes

## Why this slice
The existing Count-Min Sketch lab already supports baseline streaming counts, merging, persistence, and memory benchmarking. The weakest open item was conservative update mode, which is a practical extension often discussed in interview and systems-design contexts because it reduces collision-driven overestimation without changing the sketch size.

## Key idea
Standard Count-Min Sketch increments every hashed counter on update. Conservative update instead:
1. finds the current counter values for the item's hashed cells,
2. computes the current minimum estimate,
3. increments only the cells currently equal to that minimum.

This keeps the estimated count from rising faster than necessary when some rows are already inflated by unrelated collisions.

## Expected trade-off
- **Pros:** lower overestimation in collision-heavy streams; better demo story for approximate analytics.
- **Cons:** update path is a little slower because each increment has to inspect current row values before mutating state.

## Implementation target
Add an opt-in conservative update mode that:
- is visible in CLI output and serialized JSON state,
- remains merge-safe only with sketches using the same update strategy,
- is covered by a deterministic collision test showing lower overestimation than the standard mode.
