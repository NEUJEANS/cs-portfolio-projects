# Raft conflict repair refresh — 2026-04-15

## Refresher
- `nextIndex` is leader-side state: where the leader should start sending entries to a follower next.
- `matchIndex` is leader-side state: the highest index the leader knows a follower has replicated.
- `prevLogIndex` / `prevLogTerm` protects the log-matching property by verifying the prefix before appending.
- If a follower rejects, the leader backs `nextIndex` up and retries.
- If a follower has a conflicting suffix, that suffix must be truncated before the leader suffix is appended.

## Tiny self-test
1. **Why can't commit advancement use follower log length alone?**
   Because a longer follower log might contain divergent entries that do not match the leader.
2. **What does a rejection tell the leader?**
   The follower and leader do not yet agree on the prefix ending at `prevLogIndex`.
3. **Why is backtracking resumable for this simulator?**
   Because each retry only adjusts `nextIndex`; the rest of the scenario state stays deterministic.
