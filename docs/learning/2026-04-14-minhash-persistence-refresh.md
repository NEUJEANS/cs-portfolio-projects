# 2026-04-14 minhash persistence refresh

## Goal for this slice
Add a reusable MinHash signature index and a benchmark mode without introducing third-party dependencies.

## Refreshed concepts
- JSON is enough for a small portfolio-friendly persisted index when readability matters more than compactness.
- A saved index needs both signatures and enough metadata to explain how they were generated (`shingle_size`, `num_hashes`, `bands`, `seed`, corpus root, and timestamp).
- Benchmark output should separate exact truth from approximate candidate generation so tiny-corpus LSH misses are not mistaken for correctness bugs.

## Self-test before implementation
- Loaded the module dynamically and confirmed `find_candidate_pairs()` still behaved correctly on a tiny 3-document corpus.
- Verified the planned extension points were clean: keep `compare`/`corpus` behavior intact, then layer index build/load and benchmark helpers around the existing primitives.
