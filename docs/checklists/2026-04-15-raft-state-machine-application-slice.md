# 2026-04-15 Raft state-machine application slice checklist

- [x] confirm repo sync status before editing
- [x] identify the next weak spot after conflict repair: committed entries were not applied into any visible state machine
- [x] do brief research if needed (used Raft commit-index / last-applied model already captured in local knowledge; web search attempt was rate-limited)
- [x] write a short refresh/self-test note for `commitIndex` vs `lastApplied`
- [x] update the simulator to apply committed log entries into per-node state-machine state
- [x] expose applied state in JSON summaries so the project tells a fuller consensus story
- [x] add regression tests for commit application, healed followers, and forced-log demos
- [x] run targeted tests
- [x] review at least 3 times and fix issues found
- [x] run full tests
- [ ] run secret scan
- [ ] commit and push
- [ ] append wrap-up note
