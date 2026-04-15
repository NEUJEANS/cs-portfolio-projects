# count-min-sketch-lab

Approximate stream-frequency analysis with a Count-Min Sketch, mergeable summaries, and heavy-hitter reporting.

## Why this project matters
This lab demonstrates a classic streaming-data structure used when exact per-item counters are too expensive. It is a good portfolio project for discussing:
- probabilistic data structures
- time/space trade-offs
- approximate analytics in logs, telemetry, and event streams
- mergeable summaries for distributed systems

## Features
- configurable `epsilon` and `delta` to control width/depth
- deterministic hash seeding for repeatable experiments
- optional `--conservative-update` mode to reduce collision-driven overestimation
- build a sketch from a token stream file
- estimate frequencies for queried items
- report heavy hitters from observed stream items with exact-count reference values
- merge compatible sketches
- JSON save/load for resumable experiments
- benchmark CLI for comparing sketch memory with an exact `Counter`

## Quickstart
```bash
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py \
  --epsilon 0.05 --delta 0.01 --conservative-update \
  build projects/count-min-sketch-lab/sample_stream.txt --output cms.json

python3 projects/count-min-sketch-lab/count_min_sketch_lab.py estimate cms.json login checkout
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py heavy-hitters cms.json --threshold 10
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py \
  --epsilon 0.01 --delta 0.01 --conservative-update \
  benchmark-memory projects/count-min-sketch-lab/sample_stream.txt --sample-size 5
```

## Run tests
```bash
python3 -m pytest projects/count-min-sketch-lab/test_count_min_sketch_lab.py -q
```

## Architecture notes
- Each row uses an independent BLAKE2b-based hash stream.
- `estimate(item)` returns the minimum row count, which avoids underestimation.
- Conservative update mode increments only the currently minimum hashed cells for an item, which can reduce overcount inflation under asymmetric collisions.
- `heavy_hitters()` scans tracked observed items for demo friendliness; production variants often pair CMS with a heap or Space-Saving summary.
- `merge()` supports distributed aggregation when sketches share the same shape, seed, and update mode.
- `benchmark-memory` reports both the core sketch table footprint and the full demo object footprint so the space trade-off stays honest.
- Small streams with few unique keys can still favor an exact `Counter` in Python; the sketch becomes compelling as the key space grows or stricter memory caps matter.

## Interview talking points
- why the error is one-sided (overestimation only)
- how `epsilon` and `delta` translate to memory footprint
- when conservative update helps and why it costs a little more per insert
- trade-offs between exact counters, Count-Min Sketch, and HyperLogLog
- why mergeable summaries are useful for sharded stream processing

## Future improvements
- pair CMS with a top-k heap for true streaming heavy hitters
- ingest CSV columns or JSONL event fields directly
- export benchmark runs as CSV/JSON for repeated experiment comparisons
