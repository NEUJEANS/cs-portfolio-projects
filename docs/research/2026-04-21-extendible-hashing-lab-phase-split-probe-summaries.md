# Extendible hashing lab phase-split probe-summaries research — 2026-04-21

## Sources checked
- OpenDSA, `15.8 Analysis of Closed Hashing` — https://opendsa-server.cs.vt.edu/ODSA/Books/Everything/html/HashAnal.html
- prior repo notes on primary clustering + tombstones from `docs/research/2026-04-21-extendible-hashing-lab-clustering-preset.md`
- tool-grounded web search on expected successful vs unsuccessful search cost in linear probing

## Notes that mattered for this slice
- OpenDSA’s framing is the right portfolio story: unsuccessful search and insertion share a cost model, while successful search behaves differently because it reflects when the key originally landed in the table.
- That means the benchmark output is more convincing when it separates phases instead of collapsing all probe work into one global average.
- The strongest interview-friendly comparison is now: puts vs gets vs deletes for workload phase pressure, plus hit vs miss lookup splits for the user-visible latency story.
- Percentiles matter more than just averages for the clustering scenario because a few ugly miss paths are exactly what recruiters should notice.

## Takeaway for implementation
Expose linear-probing phase summaries in every committed artifact, not just the JSON internals: Markdown should show a small phase table, the HTML dashboard should surface a readable phase split, and the CSV should export phase columns for quick spreadsheet/chart follow-up.
