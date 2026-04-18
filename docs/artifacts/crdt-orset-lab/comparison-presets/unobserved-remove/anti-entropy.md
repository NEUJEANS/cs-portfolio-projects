# OR-Set anti-entropy report — preset unobserved-remove — Unobserved remove cannot tombstone unseen tags

Replicas: a, b, c

Story: Across 6 directional sync transfer(s), shipping whole OR-Set states would cost 338 byte(s), while delta-state transfer needs 292 byte(s), saving 46 byte(s). The largest sync delta in this run is step 3 at 105 byte(s).

## Totals

- sync steps: `3`
- directional transfers: `6`
- full-state bytes: `338`
- delta-state bytes: `292`
- bytes saved vs full-state sync: `46`

## Final replica digests

- `a` — digest `bc0df1bd11ad6d73`…, payload `64` bytes, observed tags `1`, tombstones `0`, counters `1`
- `b` — digest `bc0df1bd11ad6d73`…, payload `64` bytes, observed tags `1`, tombstones `0`, counters `1`
- `c` — digest `bc0df1bd11ad6d73`…, payload `64` bytes, observed tags `1`, tombstones `0`, counters `1`

## Sync transfer details

| Step | Event | Transfer | Digests before | Full bytes | Delta bytes | Saved | Delta payload |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | a ↔ b sync (both) | `a -> b` | `bc0df1bd11ad… vs 59accd60481d…` | 64 | 64 | 0 | tags notebook=a:1; tombstones ∅; counters a=1 |
| 3 | a ↔ b sync (both) | `b -> a` | `59accd60481d… vs bc0df1bd11ad…` | 41 | 41 | 0 | tags ∅; tombstones ∅; counters ∅ |
| 4 | b ↔ c sync (both) | `b -> c` | `bc0df1bd11ad… vs 59accd60481d…` | 64 | 64 | 0 | tags notebook=a:1; tombstones ∅; counters a=1 |
| 4 | b ↔ c sync (both) | `c -> b` | `59accd60481d… vs bc0df1bd11ad…` | 41 | 41 | 0 | tags ∅; tombstones ∅; counters ∅ |
| 5 | a ↔ c sync (both) | `a -> c` | `bc0df1bd11ad… vs bc0df1bd11ad…` | 64 | 41 | 23 | tags ∅; tombstones ∅; counters ∅ |
| 5 | a ↔ c sync (both) | `c -> a` | `bc0df1bd11ad… vs bc0df1bd11ad…` | 64 | 41 | 23 | tags ∅; tombstones ∅; counters ∅ |
