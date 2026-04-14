# Bloom filter benchmark slice research — 2026-04-14

## Goal
Add a CLI benchmark mode that compares:
- configured target false-positive rate
- formula-based estimated false-positive rate after insertions
- observed false-positive rate from generated probe tokens not inserted into the filter

## Notes
- Standard Bloom filter estimate after inserting `n` items into `m` bits with `k` hashes:
  - `(1 - exp(-k * n / m)) ^ k`
- A practical benchmark should generate two disjoint sets:
  - inserted tokens
  - probe tokens guaranteed not to be inserted
- For deterministic tests and reproducible portfolio demos, support a fixed RNG seed.
- Benchmark output should include sample sizes and both estimated/observed rates.

## CLI design
Proposed subcommand:
- `benchmark --capacity N --error-rate P --inserted-count I --probe-count J [--seed S]`

Output fields:
- `capacity`
- `target_error_rate`
- `inserted_count`
- `probe_count`
- `estimated_false_positive_rate`
- `observed_false_positive_rate`
- `false_positive_count`
- `bit_count`
- `hash_count`
- `load_factor`

## Testing focus
- deterministic benchmark result with seed
- probe count and inserted count reflected in output
- observed rate stays within `[0, 1]`
- zero false positives handled correctly
