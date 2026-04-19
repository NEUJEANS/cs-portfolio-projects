# 2026-04-19 regex engine NFA trace slice checklist

- [x] verify git sync state before editing
- [x] capture a brief research note: Russ Cox's Thompson-NFA framing is a good reminder that the active-state set and epsilon closure are the core teaching surface, so a trace view should expose those transitions directly instead of acting like a black box
- [x] capture a short refresh/self-test note: rehearse how fullmatch consumes one closure at a time, how search retries start offsets left-to-right, and where MATCH / EOL states should appear in a final trace
- [x] update the resumable project checklist state before coding
- [x] implement step-by-step JSON trace helpers for both `fullmatch` and `search`
- [x] add a `trace` CLI command with `--mode fullmatch|search`
- [x] add regression coverage for successful traces, failed early-stop traces, and leftmost-search attempt reporting
- [x] generate committed sample trace artifacts and refresh the README
- [x] run tests and smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
