# Raft Election Simulator Checklist

- [x] define a portfolio-friendly scope focused on leader election rather than full replication
- [x] refresh Raft terms, vote rules, randomized timeouts, and higher-term step-down behavior
- [x] implement deterministic node-state transitions, vote requests, and heartbeat handling
- [x] support scripted scenarios with run, isolate, heal, timeout override, and client-write actions
- [x] add focused tests for happy-path election, split-vote retry, recovery, CLI output, and commit-index behavior
- [x] add log-replication and commit-index mechanics in a follow-up slice
- [x] model prev-log-index / prev-log-term conflict repair with leader backtracking and follower suffix repair
- [x] track applied state-machine values derived from committed commands in a follow-up slice
