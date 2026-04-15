# Raft log replication refresh — 2026-04-15

## Quick refresher
- Raft leaders append client commands to their own log first, then replicate entries to followers via AppendEntries.
- An entry is considered committed once it is stored on a majority of nodes in the leader's current view.
- Followers can safely advance their commit index only up to what they have actually replicated locally.
- Heartbeats are just AppendEntries calls with zero new log items.

## Tiny self-test
1. **Why can a leader mark an entry committed before every follower has it?**
   Because Raft only needs majority durability for commitment.
2. **Why should a follower's commit index never exceed its log length?**
   Because a node cannot commit an entry it does not store.
3. **What does a partition change in this simplified simulator?**
   It blocks vote traffic and heartbeat / replication traffic for isolated nodes.

## Slice note
For this repo slice, a lightweight replication model is enough: clone the leader log onto reachable followers, compute majority replication length, then advance per-node commit indexes conservatively.
