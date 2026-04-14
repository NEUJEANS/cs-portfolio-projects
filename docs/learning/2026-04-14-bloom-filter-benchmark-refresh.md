# Bloom filter benchmark refresh — 2026-04-14

## Quick refresh
- `m = ceil(-(n * ln(p)) / (ln 2)^2)` gives bit array size.
- `k = ceil((m / n) * ln 2)` gives hash count.
- After inserts, estimated false-positive rate is `(1 - exp(-k * n / m))^k`.
- Benchmarks need probe items that were not inserted, otherwise true positives contaminate the observed false-positive rate.

## Self-test
1. If the filter is empty, estimated false-positive rate should be `0.0`.
2. If benchmark probes are disjoint from inserted items, any positive hit is a false positive.
3. With a fixed seed, benchmark output should be reproducible enough for tests.
