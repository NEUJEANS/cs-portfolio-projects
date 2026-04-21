# Extendible hashing B-tree benchmark-baseline research — 2026-04-21

## Sources checked
- PostgreSQL docs, `11.2. Index Types` — https://www.postgresql.org/docs/current/indexes-types.html
- repo-local reference: `projects/b-tree-index-lab/README.md`

## Notes that mattered for this slice
- PostgreSQL's docs make the core contrast crisp: B-tree indexes support equality **and** range comparisons on sortable keys, while hash indexes are limited to equality lookups.
- That means the repo's B-tree lab is a useful portfolio baseline for the extendible-hashing benchmark, but it should be framed as a **paged ordered-index baseline**, not as a claim that the structures solve exactly the same job.
- The local B-tree lab already exposes fixed-size page-layout math (`page_size`, `value_bytes`, node count, file bytes), which makes it a good fit for a storage-oriented benchmark summary instead of a synthetic time benchmark.
- For this project, the strongest story is: extendible hashing shows split/merge/directory behavior, cuckoo hashing shows displacement/rehash pressure, and the B-tree baseline shows what an ordered paged index would cost in height/nodes/file bytes for the same logical key/value set.

## Takeaway for implementation
Surface B-tree page metrics directly in the benchmark summary and committed artifacts, make the suite's B-tree knobs explicit for resumability, and keep the report copy honest about the B-tree baseline being page-oriented rather than a pure hash-table competitor.
