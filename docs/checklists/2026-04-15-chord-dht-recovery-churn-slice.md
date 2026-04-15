# Chord DHT recovery churn slice

- Timestamp: 2026-04-15 19:42 UTC
- Project: `projects/chord-dht-lab`
- Goal: model explicit recovery/rejoin events inside churn scenarios so the portfolio lab covers node return, not only joins and failures.

## Plan
- [x] sync repo before editing
- [x] inspect the current churn simulator for the weakest unfinished scenario gap
- [x] skip web research because recovery/rejoin events are a direct extension of the existing churn and stabilization model
- [x] do a short Python state-transition self-check
- [x] implement `recover` churn events for original nodes that previously failed
- [x] expose the new event type in sample data and README usage
- [x] add/update tests for recovery success, validation errors, and CLI behavior
- [x] run tests
- [x] review pass 1
- [x] review pass 2
- [x] review pass 3
- [x] secret scan
- [x] commit, push, wrap-up

## Notes
- Recovery should only apply to nodes from the original ring; brand-new joined nodes still use `join` if they return later.
- The recover action should fail fast when the node is still live so event files stay honest and resumable.
