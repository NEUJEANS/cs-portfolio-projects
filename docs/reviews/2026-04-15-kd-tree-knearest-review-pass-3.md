# Review Pass 3 — KD-Tree k-Nearest Slice

## Focus
- command flow, unnecessary work, and docs alignment

## Issue found
- `main()` eagerly built a KD-tree even for the benchmark path, which already constructs its own tree internally

## Fix applied
- changed CLI flow to build the KD-tree only for query commands that need it directly
- updated README usage/examples to document the new `knearest` and `benchmark` commands clearly
