# 2026-04-14 mini-mapreduce refresh

## Refresher
- Map tasks emit intermediate key/value pairs.
- A combiner can aggregate per-shard output before the global reduce step.
- Deterministic output ordering matters for reproducible tests and portfolio demos.

## Self-test
- Build one text job and one structured-data job.
- Verify shard boundaries do not change final counts.
