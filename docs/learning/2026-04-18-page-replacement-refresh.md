# Learning refresh — 2026-04-18 — page replacement lab

## Quick rules refresher
- **FIFO** evicts the page that has been resident the longest.
- **LRU** evicts the page whose most recent use is oldest.
- **OPT** evicts the page whose next use is farthest in the future (or never reused).
- **Belady's anomaly** can happen with FIFO because adding more frames does not guarantee a superset of resident pages.
- **LRU** and **OPT** are stack algorithms, so their page faults should not increase when frame counts increase.

## Self-test
Reference string: `1 2 3 4 1 2 5 1 2 3 4 5`

Expected page faults:
- FIFO with 3 frames: `9`
- FIFO with 4 frames: `10`
- LRU with 3 frames: `10`
- OPT with 3 frames: `7`

## Benchmark trace refresher
- **Phase shifts** matter because the hot working set can change between parser/codegen/optimizer-style stages; algorithms that adapt slowly may keep stale pages too long.
- **Hot-set plus scan** traces are useful because a long sequential sweep can pollute memory and expose where FIFO or Clock lag behind recency-aware policies.
- **Streaming/backfill bursts** create short cold spikes that test whether a policy protects the active window or thrashes on one-off backfills.

## Implementation note
For the first slice, a deterministic simulator with clear tie-breaking mattered more than asymptotic optimization. For the benchmark slice, longer built-in traces keep that explainability while making the gallery outputs look more like realistic systems workloads instead of only toy anomaly strings.
