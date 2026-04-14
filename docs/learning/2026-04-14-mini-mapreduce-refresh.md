# 2026-04-14 mini-mapreduce refresh

## Refresher
- Map tasks emit intermediate key/value pairs.
- A combiner can aggregate per-shard output before the global reduce step.
- A partitioner routes each key to a deterministic reducer bucket.
- Reducer skew matters because one hot bucket can dominate total runtime.
- Deterministic output ordering matters for reproducible tests and portfolio demos.

## Self-test
- Explain why a stable hash is better than Python's process-randomized `hash()` for reproducible reducer assignment.
- Verify shard boundaries do not change final counts.
- Verify reducer count changes bucket stats without changing aggregate output.

## Self-test answers
- `hash()` changes across processes, so a cryptographic digest prefix is simpler and reproducible for tests.
- Combiners are local optimizations; global counts should stay invariant.
- Reducer stats may change, but the final reduced totals should remain identical.
