# count-min-sketch-lab

Approximate stream-frequency analysis with a Count-Min Sketch, mergeable summaries, and bounded top-k candidate reporting.

## Why this project matters
This lab demonstrates a classic streaming-data structure used when exact per-item counters are too expensive. It is a good portfolio project for discussing:
- probabilistic data structures
- time/space trade-offs
- approximate analytics in logs, telemetry, and event streams
- mergeable summaries for distributed systems
- online heavy-hitter detection with bounded memory

## Features
- configurable `epsilon` and `delta` to control width/depth
- deterministic hash seeding for repeatable experiments
- optional `--conservative-update` mode to reduce collision-driven overestimation
- optional `--top-k-capacity` Space-Saving style summary for live heavy-hitter candidates
- build a sketch from a token stream file
- estimate frequencies for queried items
- report heavy hitters from observed stream items with exact-count reference values
- report tracked top-k candidates with summary estimate, summary error, CMS estimate, and exact demo count
- merge compatible sketches
- JSON save/load for resumable experiments
- benchmark CLI for comparing sketch memory with an exact `Counter`
- repeated benchmark-series export that writes resumable JSON/CSV experiment artifacts across multiple seeds

## Quickstart
```bash
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py \
  --epsilon 0.05 --delta 0.01 --conservative-update --top-k-capacity 5 \
  build projects/count-min-sketch-lab/sample_stream.txt --output cms.json

python3 projects/count-min-sketch-lab/count_min_sketch_lab.py estimate cms.json login checkout
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py heavy-hitters cms.json --threshold 10
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py top-k cms.json --limit 5
python3 projects/count-min-sketch-lab/count_min_sketch_lab.py \
  --epsilon 0.01 --delta 0.01 --conservative-update --top-k-capacity 5 \
  benchmark-memory projects/count-min-sketch-lab/sample_stream.txt --sample-size 5

python3 projects/count-min-sketch-lab/count_min_sketch_lab.py \
  --epsilon 0.01 --delta 0.01 --conservative-update --top-k-capacity 5 \
  benchmark-series projects/count-min-sketch-lab/sample_stream.txt \
  --sample-size 5 --seeds 0 1 2 3 \
  --output-json artifacts/count-min-sketch-benchmark-series.json \
  --output-csv artifacts/count-min-sketch-benchmark-series.csv
```

## Run tests
```bash
.venv/bin/python -m pytest projects/count-min-sketch-lab/test_count_min_sketch_lab.py -q
```

## Architecture notes
- Each row uses an independent BLAKE2b-based hash stream.
- `estimate(item)` returns the minimum row count, which avoids underestimation.
- Conservative update mode increments only the currently minimum hashed cells for an item, which can reduce overcount inflation under asymmetric collisions.
- The optional top-k summary follows a compact Space-Saving style design for online candidate tracking.
- `top-k` output keeps both the bounded summary estimate/error and the CMS estimate so the approximation layers are visible instead of hidden.
- `heavy_hitters()` scans tracked observed items for demo friendliness; production variants often drop exact observations and rely only on bounded summaries.
- `merge()` supports distributed aggregation when sketches share the same shape, seed, update mode, and top-k configuration.
- After merge, the demo reconstructs the retained top-k candidates from observed counts so the resumable candidate list remains trustworthy.
- `benchmark-memory` reports both the core sketch table footprint and the full demo object footprint so the space trade-off stays honest.
- `benchmark-series` repeats the measurement across hash seeds and emits chart-friendly artifacts so comparisons are resumable instead of one-off terminal snapshots.
- Small streams with few unique keys can still favor an exact `Counter` in Python; the sketch becomes compelling as the key space grows or stricter memory caps matter.

## Interview talking points
- why the error is one-sided (overestimation only)
- how `epsilon` and `delta` translate to memory footprint
- when conservative update helps and why it costs a little more per insert
- why CMS benefits from a bounded candidate summary for top-k reporting
- trade-offs between exact counters, Count-Min Sketch, Space-Saving, and HyperLogLog
- why mergeable summaries are useful for sharded stream processing

## Future improvements
- ingest CSV columns or JSONL event fields directly
- compare CMS top-k candidates with exact top-k under different skew patterns
- compare CMS top-k candidates with exact top-k under different skew patterns
