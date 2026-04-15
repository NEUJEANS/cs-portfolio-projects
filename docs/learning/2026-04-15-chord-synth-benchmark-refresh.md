# Chord synthetic benchmark refresh — 2026-04-15

## Quick refresh
- Deterministic synthetic fixtures are better than ad-hoc random demos because benchmark diffs stay attributable to code changes.
- For a Chord ring, synthetic node generation must guard against identifier collisions after hashing into the `m`-bit space.
- Benchmark payloads should record the seed and effective benchmark start set so runs are reproducible.

## Self-test
- Q: Why not just generate node names sequentially without checking hashes?
  - A: Different names can still collide after hashing into a small ring, so the generator must verify unique IDs.
- Q: What makes the synthetic benchmark resumable?
  - A: The CLI output includes `seed`, `m_bits`, node/key counts, generated nodes/keys, and benchmark summary so the same run can be reproduced exactly.
