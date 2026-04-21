# extendible-hashing-lab B-tree benchmark self-test — 2026-04-21

## Quick refresh
- extendible hashing is strongest when the benchmark explains directory growth, local-depth splits, merges, and shrink events
- cuckoo hashing is the insertion-pressure contrast because it pays with displacement chains and occasional rehashes
- a B-tree baseline adds a storage/index-layout contrast: height, node count, and paged file bytes for the same final logical records
- if the CLI accepts a report title override, every outward-facing artifact should agree on it so saved JSON/stdout/Markdown outputs stay consistent

## Self-test
1. **Q:** Why is the B-tree comparison useful even though it is not another hash table?
   **A:** It gives the portfolio project an ordered, paged index baseline that highlights different tradeoffs: range-friendly structure and page footprint versus extendible hashing's directory-driven equality path.
2. **Q:** What should stay deterministic across repeated benchmark exports here?
   **A:** The extendible and B-tree metrics plus the rendered JSON/Markdown/CSV artifacts, because the workload order and both implementations are deterministic in this lab.
3. **Q:** Why should the suite JSON carry explicit B-tree knobs instead of relying only on code defaults?
   **A:** So the committed benchmark artifacts are reproducible and self-describing even if someone revisits the project later without remembering the code defaults.
