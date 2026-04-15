# Raft conflict repair research — 2026-04-15

## Goal
Add a stronger portfolio slice to `raft-election-simulator` by modeling the `prevLogIndex` / `prevLogTerm` check that leaders use to repair diverged follower logs.

## Key points
- Leaders send `AppendEntries` with a `prevLogIndex` and `prevLogTerm` describing the entry immediately before the new suffix.
- Followers reject the append if they do not have that index or if the term at that index differs.
- Leaders keep a per-follower `nextIndex` and back it up after each rejection until a shared prefix is found.
- Once the shared prefix is found, followers delete their conflicting suffix and append the leader's entries.
- Commitment still depends on majority replication, so commit tracking should use per-follower matched indexes rather than raw log lengths.

## Slice decision
Implement a lightweight but faithful version:
1. Track `next_index` and `match_index` per follower for the current leader.
2. Retry append attempts with decreasing `next_index` when followers reject.
3. Truncate conflicting follower suffixes before appending the leader suffix.
4. Advance commit index from majority `match_index` values.

## Sources consulted
- Raft paper summaries and engineering explainers describing `AppendEntries`, `prevLogIndex`, and backtracking repair.
- General consensus references emphasizing the log-matching property and majority-based commit advancement.
