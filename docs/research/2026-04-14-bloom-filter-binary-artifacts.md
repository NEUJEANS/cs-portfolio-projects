# Bloom filter binary artifact slice — 2026-04-14

## Why this slice
The Bloom filter project already covered membership checks, benchmarks, and a counting variant. The weakest remaining portfolio gap was artifact realism: large probabilistic structures should not have to live only as human-readable JSON.

## Chosen design
- Keep JSON as the default editable/resumable format.
- Add a compact binary export format for both standard and counting filters.
- Preserve enough metadata in a small JSON header block so binary files stay versionable and debuggable.
- Store the payload separately:
  - standard filter: packed bitset bytes
  - counting filter: fixed-width counters using `ceil(counter_bits / 8)` bytes each

## Tradeoffs
- This is meaningfully smaller than JSON while still simple to reason about.
- Counting filters remain much larger than standard filters because delete support needs counters rather than single bits.
- The current binary format uses whole bytes per counter instead of sub-byte packing; that keeps the code clear and robust, with room for future compression work.

## Benchmark note
Using `capacity=1000`, `error_rate=0.01`, `inserted_count=800`, `counter_bits=8`:
- standard JSON: 2546 bytes
- standard binary: 1322 bytes
- counting JSON: 67306 bytes
- counting binary: 9750 bytes
- counting binary / standard binary: about 7.38x

## Outcome
This turns the project from a purely instructional Bloom filter demo into something closer to a systems artifact pipeline: build, persist, export compactly, reload, inspect, and compare tradeoffs.
