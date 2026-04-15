# Count-Min Sketch Top-K Refresh + Self-Test

Date: 2026-04-15

## Refresher
- CMS update: increment one counter per row.
- CMS query: estimate with the minimum hashed counter across rows.
- CMS guarantee: no underestimation, bounded overestimation.
- Space-Saving summary: keep at most `m` tracked keys; when a miss arrives and the summary is full, replace the minimum-count key and record its previous count as the new key's error.

## Why pair them
- CMS alone can estimate any queried key but does not keep a compact candidate list for top-k.
- Space-Saving alone keeps a compact candidate list but is not mergeable in the same way as CMS.
- Together they make the demo more realistic for stream analytics interviews.

## Self-test
1. Why does CMS never underestimate in an insertion-only stream?
   - Because every occurrence increments all hashed counters for the item, so the minimum hashed counter cannot fall below the true count.
2. Why is a bounded candidate summary needed for streaming top-k?
   - Because the stream may contain too many unique keys to retain all of them exactly while still reporting the most frequent ones online.
3. What happens when a new item arrives and the Space-Saving summary is full?
   - It replaces the currently minimum-count entry, receives count `min_count + increment`, and stores `min_count` as its error bound.
4. What trade-off does this slice introduce?
   - More helpful top-k reporting and interview value in exchange for a small amount of extra per-update work and extra serialized state.
