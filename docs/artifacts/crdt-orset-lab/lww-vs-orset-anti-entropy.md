# OR-Set anti-entropy report — script sample_compare_ops.json

Replicas: a, b, c

Story: Across 8 directional sync transfer(s), shipping whole OR-Set states would cost 535 byte(s), while delta-state transfer needs 430 byte(s), saving 105 byte(s). The largest sync delta in this run is step 5 at 128 byte(s).

## Totals

- sync steps: `4`
- directional transfers: `8`
- full-state bytes: `535`
- delta-state bytes: `430`
- bytes saved vs full-state sync: `105`

## Final replica digests

- `a` — digest `ce1b93dbe7b4c17b`…, payload `81` bytes, observed tags `2`, tombstones `1`, counters `2`
- `b` — digest `ce1b93dbe7b4c17b`…, payload `81` bytes, observed tags `2`, tombstones `1`, counters `2`
- `c` — digest `ce1b93dbe7b4c17b`…, payload `81` bytes, observed tags `2`, tombstones `1`, counters `2`

## Sync transfer details

| Step | Event | Transfer | Digests before | Full bytes | Delta bytes | Saved | Delta payload |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | a ↔ b sync (both) | `a -> b` | `bc0df1bd11ad… vs 59accd60481d…` | 64 | 64 | 0 | tags notebook=a:1; tombstones ∅; counters a=1 |
| 2 | a ↔ b sync (both) | `b -> a` | `59accd60481d… vs bc0df1bd11ad…` | 41 | 41 | 0 | tags ∅; tombstones ∅; counters ∅ |
| 5 | c ↔ a sync (both) | `c -> a` | `640eb733189d… vs bc0df1bd11ad…` | 64 | 64 | 0 | tags notebook=c:1; tombstones ∅; counters c=1 |
| 5 | c ↔ a sync (both) | `a -> c` | `bc0df1bd11ad… vs 640eb733189d…` | 64 | 64 | 0 | tags notebook=a:1; tombstones ∅; counters a=1 |
| 6 | a ↔ b sync (both) | `a -> b` | `b579452ba051… vs 88a4f152f33f…` | 76 | 64 | 12 | tags notebook=c:1; tombstones ∅; counters c=1 |
| 6 | a ↔ b sync (both) | `b -> a` | `88a4f152f33f… vs b579452ba051…` | 69 | 46 | 23 | tags ∅; tombstones a:1; counters ∅ |
| 7 | a ↔ c sync (both) | `a -> c` | `ce1b93dbe7b4… vs b579452ba051…` | 81 | 46 | 35 | tags ∅; tombstones a:1; counters ∅ |
| 7 | a ↔ c sync (both) | `c -> a` | `b579452ba051… vs ce1b93dbe7b4…` | 76 | 41 | 35 | tags ∅; tombstones ∅; counters ∅ |
