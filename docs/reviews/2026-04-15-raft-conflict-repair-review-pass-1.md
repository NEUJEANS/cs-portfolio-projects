# Review pass 1 — static replication logic audit

## Focus
Read the Raft replication changes for correctness around leader-side follower tracking.

## Findings
1. Commit advancement should be derived from replicated match indexes, not raw follower log lengths.
2. Leader state needed explicit per-follower `next_index` / `match_index` storage so retries stay deterministic.

## Fixes applied
- Added `replication_state` keyed by leader and follower.
- Switched commit advancement to majority `match_index` values.
- Logged append rejections and successful retry metadata for easier debugging.

## Result
Core replication flow now models the intended backtracking behavior instead of replacing follower logs wholesale.
