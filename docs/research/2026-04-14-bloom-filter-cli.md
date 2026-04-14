# Bloom Filter CLI research — 2026-04-14

## Why this project
- Adds a probabilistic data structure project missing from the current portfolio set.
- Demonstrates hashing, space/time tradeoffs, false-positive reasoning, and serialization.
- Gives interview-friendly talking points beyond standard CRUD/CLI apps.

## Key ideas
- Bloom filters support fast membership checks with no false negatives and possible false positives.
- Approximate false-positive rate after inserting `n` items into `m` bits with `k` hashes:
  `p = (1 - e^(-kn/m))^k`
- Good parameter choices for expected capacity `n` and target error rate `p`:
  - `m = -(n * ln(p)) / (ln(2)^2)`
  - `k = (m / n) * ln(2)`
- Double hashing is a practical way to derive multiple bit positions from two digest values instead of computing many independent hashes.

## Portfolio-worthy slice for this run
- Create a reusable Bloom filter implementation in Python.
- Add a CLI for building, querying, and inspecting a saved filter.
- Include JSON serialization so the artifact can be reused between runs.
- Validate the math and behavior with tests.
