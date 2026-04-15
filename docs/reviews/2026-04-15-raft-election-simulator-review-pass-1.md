# Raft election simulator review pass 1 — 2026-04-15

## Focus
Replication / step-down control flow.

## Issue found
`broadcast_heartbeat()` could continue into commit-index refresh even after the leader had stepped down because of a higher-term follower.

## Fix applied
Stopped the heartbeat loop early when the sender is no longer a leader, so stale leaders do not continue replication-side bookkeeping.

## Verification
- `python3 -m unittest projects/raft-election-simulator/test_raft_election.py`
