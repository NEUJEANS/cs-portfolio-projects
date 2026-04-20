# extendible-hashing-lab benchmark self-test — 2026-04-20

## Quick refresh
- extendible hashing pays for clustered inserts with bucket splits and directory growth, but stable lookups stay local once the directory is shaped
- cuckoo hashing aims for worst-case `O(1)` lookup by allowing insertion-time displacement chains and occasional full-table rehashes
- a good comparison suite should include at least one stable read-heavy case, one collision/split-pressure case, and one delete-heavy churn case
- for this lab, extendible metrics should stay deterministic across repeated trials because the algorithm is not seeded; only the cuckoo side should vary across seeded trials

## Self-test
1. **Q:** Why should repeated extendible-hashing trials agree exactly on split/merge/growth counts for the same scenario?
   **A:** The benchmark feeds the same ordered operations into a deterministic hash/index implementation, so any drift would signal a bug in summary logic or state handling.
2. **Q:** What tradeoff makes cuckoo hashing worth comparing here?
   **A:** It often keeps lookups simple and compact, but difficult insert patterns can trigger displacement chains or a table-wide rehash that extendible hashing avoids.
3. **Q:** What metric makes extendible hashing's delete story stronger than a simple load-factor chart?
   **A:** Directory shrink count, because it shows the index can reclaim prefix width after delete-heavy churn instead of only growing forever.
