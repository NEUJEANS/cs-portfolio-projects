# 2026-04-15 Raft conflict repair slice checklist

- [x] confirm repo sync status before editing
- [x] do brief research on `prevLogIndex` / `prevLogTerm` repair
- [x] refresh `nextIndex` / `matchIndex` behavior with a tiny self-test note
- [x] identify the next unfinished item in `raft-election-simulator`
- [x] implement follower rejection, leader backtracking, and conflicting-suffix truncation
- [x] update majority commit advancement to use replicated match indexes
- [x] add regression coverage for divergent follower repair
- [x] run tests
- [x] perform 3 review passes and fix issues found
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up note
