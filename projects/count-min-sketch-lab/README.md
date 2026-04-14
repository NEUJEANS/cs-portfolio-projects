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
- build a sketch from a token stream file
- estimate frequencies for queried items
- report heavy hitters from observed stream items with exact-count reference values
- merge compatible sketches
- JSON save/load for resumable experiments

## Quickstart
```bash
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py   --epsilon 0.05 --delta 0.01   build sample_stream.txt --output cms.json

python3 projects/count-min-sketch-lab/count_min_sketch_lab.py estimate cms.json login checkout
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py heavy-hitters cms.json --threshold 10
```

## Run tests
```bash
python3 -m pytest projects/count-min-sketch-lab/test_count_min_sketch_lab.py -q
```

## Architecture notes
- Each row uses an independent BLAKE2b-based hash stream.
- `estimate(item)` returns the minimum row count, which avoids underestimation.
- `heavy_hitters()` scans tracked observed items for demo friendliness; production variants often pair CMS with a heap or Space-Saving summary.
- `merge()` supports distributed aggregation when sketches share the same shape and seed.

## Interview talking points
- why the error is one-sided (overestimation only)
- how `epsilon` and `delta` translate to memory footprint
- trade-offs between exact counters, Count-Min Sketch, and HyperLogLog
- why mergeable summaries are useful for sharded stream processing

## Future improvements
- add conservative update mode to reduce overcount inflation
- pair CMS with a top-k heap for true streaming heavy hitters
- benchmark memory savings versus `collections.Counter`
- ingest CSV columns or JSONL event fields directly
