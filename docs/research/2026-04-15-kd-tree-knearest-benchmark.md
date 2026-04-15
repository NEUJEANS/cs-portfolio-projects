# KD-Tree k-Nearest + Benchmark Research

## Notes
- k-nearest KD-tree search typically keeps a bounded priority queue of the best candidates found so far while exploring the more promising subtree first.
- The opposite subtree still has to be explored when the query point is within the current worst-candidate radius of the splitting plane.
- Benchmarks are only trustworthy when the KD-tree answers are cross-checked against a brute-force baseline for the same generated queries.
- Reproducible benchmark seeds are useful for portfolio demos because they keep timing comparisons explainable and easy to rerun.

## Planned slice
- add `knearest` CLI support
- add a benchmark command that generates repeatable random queries inside dataset bounds
- validate benchmark results against brute force before reporting speedup
