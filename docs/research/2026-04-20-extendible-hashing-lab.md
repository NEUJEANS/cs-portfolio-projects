# Extendible hashing lab research — 2026-04-20

## Source checked
- Wikipedia, "Extendible hashing" (`https://en.wikipedia.org/wiki/Extendible_hashing`)

## Notes that matter for this slice
- extendible hashing grows one bucket at a time instead of rebuilding the full table, which makes it a good portfolio contrast with whole-table rehashing approaches
- the directory uses hash-bit prefixes (or suffixes, depending on implementation); this slice uses low-order bits for the directory index because it keeps the implementation and tests straightforward
- `global_depth` controls directory width, while each bucket tracks its own `local_depth`
- when an overflowing bucket already matches `global_depth`, the directory must double before the split can repoint only the affected aliases
- when `local_depth < global_depth`, only the aliases that point at the overflowing bucket need to be repointed during a split

## Takeaway for implementation
Focus the first vertical slice on: deterministic hashing, bucket split correctness, clear directory inspection output, persisted snapshots, and tests that prove both bucket-level and directory-level growth behavior.
