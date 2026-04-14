# 2026-04-14 Raft Election Refresh

## Quick refresh
- Each server is in one of three roles: follower, candidate, or leader.
- Followers become candidates when they stop hearing heartbeats before their election timeout.
- Candidates increment term, vote for themselves, request votes, and win with a strict majority.
- Randomized election timeouts reduce the chance of permanent split votes.
- Any node that learns about a higher term steps down to follower.
- Leaders send heartbeats periodically to suppress new elections.

## Self-test
1. Why do randomized timeouts help? They stagger candidate starts so one candidate can often collect a majority before others begin.
2. What forces a stale leader to step down? Seeing a message from a node with a higher term.
3. Why is a majority required? It prevents two disjoint groups from both electing leaders in the same term.
