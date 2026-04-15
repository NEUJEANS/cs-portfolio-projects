# Raft state-machine application research — 2026-04-15

## Goal
Upgrade `raft-election-simulator` so committed log entries do not just replicate; they also produce visible state-machine results.

## Key points
- Raft conceptually separates log replication from state-machine application.
- `commitIndex` marks entries known to be durable by majority agreement.
- `lastApplied` tracks which committed entries a node has already executed.
- A compact simulator can model this with deterministic per-node application after commit advancement.
- For this teaching-oriented lab, parsing simple `set key=value` commands is enough to demonstrate replicated state convergence.

## Slice decision
1. Add `last_applied`, `state_machine`, and `applied_commands` to each node summary.
2. Apply committed entries whenever leader or follower commit indexes move forward.
3. Keep unsupported commands visible in `applied_commands` without forcing a fake key/value mutation.
4. Extend tests to prove state convergence after normal replication, healing, and forced-log demos.

## Notes
- I attempted a web-search refresh first, but the configured search provider hit quota limits, so this slice uses standard Raft semantics and the repo's existing local notes.
