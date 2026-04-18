# OR-Set anti-entropy report — preset observed-remove-sync — Observed remove yields the same final answer

Replicas: a, b, c

Story: Across 8 directional sync transfer(s), shipping whole OR-Set states would cost 486 byte(s), while delta-state transfer needs 384 byte(s), saving 102 byte(s). The largest sync delta in this run is step 4 at 110 byte(s).

## Totals

- sync steps: `4`
- directional transfers: `8`
- full-state bytes: `486`
- delta-state bytes: `384`
- bytes saved vs full-state sync: `102`

## Final replica digests

- `a` — digest `88a4f152f33fd9c8`…, payload `69` bytes, observed tags `1`, tombstones `1`, counters `1`
- `b` — digest `88a4f152f33fd9c8`…, payload `69` bytes, observed tags `1`, tombstones `1`, counters `1`
- `c` — digest `88a4f152f33fd9c8`…, payload `69` bytes, observed tags `1`, tombstones `1`, counters `1`

## Sync transfer details

| Step | Event | Transfer | Digests before | Full bytes | Delta bytes | Saved | Delta payload |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | a ↔ b sync (both) | `a -> b` | `bc0df1bd11ad… vs 59accd60481d…` | 64 | 64 | 0 | tags notebook=a:1; tombstones ∅; counters a=1 |
| 2 | a ↔ b sync (both) | `b -> a` | `59accd60481d… vs bc0df1bd11ad…` | 41 | 41 | 0 | tags ∅; tombstones ∅; counters ∅ |
| 4 | b ↔ c sync (both) | `b -> c` | `88a4f152f33f… vs 59accd60481d…` | 69 | 69 | 0 | tags notebook=a:1; tombstones a:1; counters a=1 |
| 4 | b ↔ c sync (both) | `c -> b` | `59accd60481d… vs 88a4f152f33f…` | 41 | 41 | 0 | tags ∅; tombstones ∅; counters ∅ |
| 5 | a ↔ b sync (both) | `a -> b` | `bc0df1bd11ad… vs 88a4f152f33f…` | 64 | 41 | 23 | tags ∅; tombstones ∅; counters ∅ |
| 5 | a ↔ b sync (both) | `b -> a` | `88a4f152f33f… vs bc0df1bd11ad…` | 69 | 46 | 23 | tags ∅; tombstones a:1; counters ∅ |
| 6 | a ↔ c sync (both) | `a -> c` | `88a4f152f33f… vs 88a4f152f33f…` | 69 | 41 | 28 | tags ∅; tombstones ∅; counters ∅ |
| 6 | a ↔ c sync (both) | `c -> a` | `88a4f152f33f… vs 88a4f152f33f…` | 69 | 41 | 28 | tags ∅; tombstones ∅; counters ∅ |
