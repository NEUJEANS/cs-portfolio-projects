# LSM Tree Bloom Filter Benchmark Notes

Date: 2026-04-15

## Why this slice
The project already had Bloom filters in the read path, but the README still described the memory/false-positive tradeoff mostly in words. A tiny benchmark/report command makes the tradeoff concrete during a portfolio walkthrough.

## Brief research takeaways
- Bloom filters are useful in storage engines because they cheaply reject negative lookups before expensive table reads.
- The standard approximate false-positive formula is `(1 - e^(-kn/m))^k`, where `m` is filter bits, `n` is inserted items, and `k` is the hash count.
- With an approximately optimal number of hashes, the false-positive rate drops as bits per key rises, at the cost of more memory.
- Around 9-10 bits per key is a common practical target when you want a low single-digit or roughly 1% false-positive rate.

## Sources consulted
- YugabyteDB storage-engine Bloom filter explanation: https://yugabytedb.tips/how-bloom-filters-supercharge-query-performance-in-yugabytedbs-docdb/
- AWS database blog overview: https://aws.amazon.com/blogs/database/implement-fast-space-efficient-lookups-using-bloom-filters-in-amazon-elasticache/
- General formula refresher: https://en.wikipedia.org/wiki/Bloom_filter

## Implementation direction chosen
- keep the benchmark deterministic and lightweight instead of timing-sensitive
- report both observed false positives and the estimated false-positive rate from the standard formula
- compare multiple bits-per-key options in one command so the result is easy to discuss in interviews or README demos
