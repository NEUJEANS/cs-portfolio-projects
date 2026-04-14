# Cache Simulator

A trace-driven cache simulator for portfolio use. It models set-associative caches, LRU replacement, and both write-back and write-through policies so students can demonstrate computer architecture fundamentals with runnable code and tests.

## Features
- configurable cache geometry: cache size, block size, associativity, set count
- address decoding into block / set / tag / offset
- set-associative lookup with LRU eviction
- write-back and write-through behavior
- JSON trace input and optional JSON result output
- deterministic tests for mapping, eviction, and memory traffic

## Trace format
Provide a JSON array of operations:

```json
[
  {"op": "read", "address": 0},
  {"op": "write", "address": 16},
  {"op": "read", "address": 64}
]
```

## Usage

```bash
python cache_simulator.py sample_trace.json \
  --cache-size 64 \
  --block-size 16 \
  --associativity 2
```

A ready-to-run `sample_trace.json` is included in this folder.

Write-through mode:

```bash
python cache_simulator.py sample_trace.json \
  --cache-size 64 \
  --block-size 16 \
  --associativity 2 \
  --write-policy write-through
```

JSON output:

```bash
python cache_simulator.py sample_trace.json \
  --cache-size 64 \
  --block-size 16 \
  --associativity 2 \
  --json
```

## Test

```bash
python3 -m unittest -v projects/cache-simulator/test_cache_simulator.py
```

## Why it is portfolio-worthy
This project shows more than CRUD: it turns core systems concepts into a simulator with explicit metrics, trace parsing, and testable behavior. It fits well in a CS student portfolio for architecture, operating systems, and performance-oriented coursework.

## Future improvements
- add FIFO and random replacement policies
- support no-write-allocate vs write-allocate modes
- accept larger trace formats from teaching assignments
- export per-access timelines or visualization-friendly data
