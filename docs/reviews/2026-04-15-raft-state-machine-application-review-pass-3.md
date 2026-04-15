# Review Pass 3 — Raft state-machine application

- Audited edge cases around the `force-log` teaching/demo path.
- Found a stale-state bug risk: forcing a fresh log onto a node could leave previously applied state-machine values behind.
- Fix applied: `force_log` now resets `last_applied`, `state_machine`, and `applied_commands` before replaying the committed prefix, and the regression test was tightened to prove the reset.
