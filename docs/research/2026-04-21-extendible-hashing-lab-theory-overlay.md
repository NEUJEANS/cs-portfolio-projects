# Extendible hashing lab theory-overlay research — 2026-04-21

## Sources checked
- Princeton Algorithms, `Hash Tables` — https://algs4.cs.princeton.edu/34hash/
- OpenDSA, `15.8 Analysis of Closed Hashing` — https://opendsa-server.cs.vt.edu/ODSA/Books/Everything/html/HashAnal.html
- repo-local benchmark context: `projects/extendible-hashing-lab/benchmark_suite.json`

## Notes that mattered for this slice
- Under linear probing, classic expected probe costs are commonly summarized as `0.5 * (1 + 1 / (1 - α))` for successful searches and `0.5 * (1 + 1 / (1 - α)^2)` for unsuccessful searches/inserts.
- OpenDSA explicitly frames successful-search cost as the better comparison for deletes/lookups and unsuccessful-search cost as the better comparison for inserts and misses, which matches the benchmark split already tracked in this repo.
- The theory reference should be described as a compact expectation, not as ground truth, because the benchmark workloads intentionally include clustering and tombstone pressure that can drive observed miss probes above the textbook average.
- For portfolio storytelling, a small overlay that compares observed hit/miss averages against the expected values is more useful than a wall of derivation because it helps reviewers connect the benchmark to familiar data-structures formulas quickly.

## Takeaway for implementation
Add a theory-overlay block per benchmark scenario, surface it in the JSON/Markdown/HTML exports, and also carry the key theory-vs-observed fields into the CSV so the committed artifact bundle stays consistent for screenshots, spreadsheet slicing, and follow-up analysis.
