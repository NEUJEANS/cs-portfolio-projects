# LSM Tree Bloom Filter Benchmark Refresh

Date: 2026-04-15

## Refreshed concepts
- `m = bits`, `n = inserted items`, and `k = hash functions` are the three parameters that drive Bloom filter behavior.
- The estimated false-positive rate is approximately `(1 - e^(-kn/m))^k`.
- Increasing bits per key lowers false positives, but it also increases filter memory.
- For this portfolio project, deterministic benchmark output is more useful than noisy wall-clock timing.

## Self-test
1. **Why compare multiple bits-per-key options in one run?**  
   Because the user can see the memory/accuracy tradeoff directly instead of guessing from a single configuration.
2. **Why include both observed and estimated false-positive rates?**  
   The observed rate grounds the report in executable behavior, while the estimate explains the expected trend mathematically.
3. **Why not benchmark elapsed time only?**  
   Tiny local timing tests are noisy and machine-dependent; false-positive counts are stable and easier to explain.
4. **Why is this still relevant to an LSM tree even though the command builds a synthetic filter?**  
   The read path uses the same Bloom filter sizing logic, so the benchmark helps justify the default configuration and explain the storage-engine tradeoff.
