# Distance Vector Routing Lab Learning Refresh — 2026-04-15

## Short refresh
- Python `dataclasses` fit immutable-ish routing entries and topology events cleanly.
- For deterministic CLI artifacts, sort router names and destination keys before serializing.
- A round-based simulator is easier to test than a timer-based one because each iteration is reproducible.
- Use a large configurable integer as the infinity metric instead of `math.inf` so poisoned advertisements serialize cleanly to JSON.

## Self-test
1. Can the next hop for a destination differ from the advertising neighbor? Yes — the neighbor is only the candidate relay; the installed next hop becomes that neighbor if it wins the route comparison.
2. What changes with split horizon? A router suppresses a destination when advertising to the same neighbor it currently uses as next hop for that destination.
3. What changes with poison reverse? Instead of suppressing that destination, the router advertises it with the configured infinity metric.
4. Why use round snapshots? They avoid order-dependent behavior within a single propagation cycle and make convergence assertions stable in tests.
