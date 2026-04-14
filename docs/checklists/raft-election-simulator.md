# Raft Election Simulator Checklist

- [x] define a portfolio-friendly scope focused on leader election rather than full replication
- [x] refresh Raft terms, vote rules, randomized timeouts, and higher-term step-down behavior
- [x] implement deterministic node-state transitions, vote requests, and heartbeat handling
- [x] support scripted scenarios with run, isolate, heal, and timeout override actions
- [x] add focused tests for happy-path election, split-vote retry, recovery, and CLI output
- [ ] add log-replication and commit-index mechanics in a future slice
