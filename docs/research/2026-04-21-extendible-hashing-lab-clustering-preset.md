# Extendible hashing lab clustering-preset research — 2026-04-21

## Sources checked
- Princeton Algorithms, `Hash Tables` — https://algs4.cs.princeton.edu/34hash/
- NIST DADS, `primary clustering` — https://xlinux.nist.gov/dads/HTML/primaryClustering.html
- tool-grounded web search on linear probing primary clustering, tombstones, and rebuild behavior

## Notes that mattered for this slice
- Linear probing is most convincing as a teaching baseline when the benchmark makes probe-sequence growth obvious rather than leaving it buried in average-case random inserts.
- NIST's primary-clustering note is the concise framing to preserve in project docs: linear probing is especially susceptible because long filled runs raise average search cost.
- Tombstones are necessary for correctness after deletes, but they also keep unsuccessful lookups expensive until a rebuild compacts the table.
- For a portfolio-friendly benchmark preset, the best demo is not “max out every structure,” but “force one memorable failure mode” so the exported JSON/Markdown/HTML/CSV artifacts tell a clean story.

## Takeaway for implementation
Add one deterministic benchmark scenario whose keys intentionally collide in the linear-probing table, mix in deletes before cleanup, and keep the operation sequence short enough that recruiters can understand why probe counts and rebuilds spike from the exported report alone.
