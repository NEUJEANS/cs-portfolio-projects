# Extendible hashing benchmark-suite research — 2026-04-20

## Sources checked
- GeeksforGeeks, `Extendible Hashing (Dynamic approach to DBMS)`
- GeeksforGeeks, `Cuckoo Hashing - Worst case O(1) Lookup!`
- repo-local reference: `projects/cuckoo-hashing-lab/README.md`

## Notes that mattered for this slice
- extendible hashing is most compelling when the report shows *why* the directory grows or shrinks, not just the final load factor
- cuckoo hashing is the right first comparison baseline for this repo because the project already exists locally, has deterministic CLI/test coverage, and highlights a contrasting insertion story: displacement and rehashing instead of directory aliasing
- a portfolio-friendly benchmark suite should include: a stable read-heavy cache-like case, a collision-heavy growth case, and a delete-heavy churn case
- for repeated benchmark trials, extendible-hashing metrics should stay identical while cuckoo metrics may vary by trial because the benchmark intentionally seeds the cuckoo salts per trial

## Takeaway for implementation
Make the benchmark summary surface extendible-specific metrics (splits, merges, directory grows/shrinks) alongside cuckoo rehash/displacement counts, and fail loudly if repeated trials ever produce inconsistent extendible metrics.
