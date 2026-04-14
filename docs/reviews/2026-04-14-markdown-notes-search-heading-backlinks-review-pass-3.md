# Review pass 3 — cache/data-shape audit

Date: 2026-04-14
Project: `markdown-notes-search`

## What I checked
- whether cached entries now persist the new metadata fields cleanly
- whether older cache payloads are safely ignored instead of partially reused
- whether backlink enrichment happens after index assembly so cached and uncached runs stay consistent

## Findings
- cache payload is versioned and rewritten with the enriched note records
- backlink enrichment is applied after indexing and before cache save, so cached runs preserve the same graph data
- invalid or older-version cache payloads fall back to a clean rebuild path
- no new issues found in this pass
