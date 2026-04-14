# Bloom filter Python refresh — 2026-04-14

## Quick refresh
- Use `hashlib.sha256` and derive multiple indexes via double hashing.
- Store the bitset as a Python integer for compactness and easy serialization.
- Clamp computed bit-size/hash-count to at least 1.
- Distinguish carefully between:
  - configured target error rate
  - estimated theoretical error rate for current inserted count
  - observed false positives from a test sample

## Self-check
1. Why no false negatives? Because inserted elements set every required bit and membership only fails when any required bit is absent.
2. Why can false positives happen? Different elements can set overlapping bits.
3. Why use double hashing? Fewer digest computations while still spreading positions well enough for this educational project.
