# Raft state-machine application refresh — 2026-04-15

## Refresher
- `commitIndex` says how far the replicated log is safely committed.
- `lastApplied` says how far a node has actually executed entries into its local state machine.
- A healthy implementation eventually drives `lastApplied` forward until it reaches `commitIndex`.
- Repaired followers should apply newly committed entries after their logs catch up.
- For demo-friendly summaries, exposing applied key/value state is more persuasive than showing raw log entries alone.

## Tiny self-test
1. **Why track `lastApplied` separately from `commitIndex`?**
   Because an entry can be committed before the node has actually executed it into local state.
2. **What should happen after a healed follower receives missing committed entries?**
   Its `commitIndex` advances, then it applies those entries and updates `lastApplied`.
3. **Why is this a good portfolio slice?**
   It closes the loop from replication to visible state changes, which makes the consensus demo easier to explain and verify.
