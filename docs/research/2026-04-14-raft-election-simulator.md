# 2026-04-14 Raft Election Simulator Research

## Goal
Add a distributed-systems project that is stronger than a generic CRUD app but still finishable in resumable slices.

## Notes
- Raft leader election is a good portfolio topic because it demonstrates consensus-system fundamentals without requiring a full production-grade cluster.
- The first slice should focus on follower/candidate/leader transitions, randomized election timeouts, majority votes, and heartbeat stabilization.
- Recovery behavior matters: stale leaders should step down when they encounter a higher term.
- Deterministic scripted scenarios are more portfolio-friendly than a purely random simulation because they are testable and demoable.

## Chosen slice
Build an in-memory simulator with JSON scenarios, node isolation controls, timeout overrides, event logs, and tests for election success, split-vote retry, and partition recovery.
