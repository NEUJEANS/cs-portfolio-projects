# Bloom filter counting variant notes — 2026-04-14

## Why this slice
The existing Bloom filter project already covered standard membership queries and benchmarked false positives. The most meaningful next vertical slice was adding a counting Bloom filter variant so the project can also demonstrate approximate deletion.

## Design decisions
- Keep the existing standard Bloom filter intact for the simplest space-efficient path.
- Add a separate `CountingBloomFilter` variant instead of overloading the standard bitset format.
- Store counters directly in JSON for readability and resumability even though a binary format would be more compact.
- Default to 8-bit counters to reduce accidental overflow during demos and small experiments.

## Tradeoffs captured in the implementation
- Deletion is only supported for counting filters, not standard filters.
- False positives are still possible, so deleting an item is approximate in the same probabilistic sense as membership checks.
- Counter overflow should fail loudly so users know to rebuild with a larger counter size or capacity.

## Follow-up opportunities
- Add a binary serialization format for large counting filters.
- Add a bulk remove mode from newline-delimited files.
- Compare memory overhead between standard and counting variants in a benchmark note.
