# Review Pass 2 - Raft Election Simulator

- Reviewed state transitions for stale leaders and candidates.
- Found that higher-term heartbeats needed to demote an old leader explicitly.
- Fix applied: heartbeat handling now converts a stale leader back to follower when it encounters a higher term.
