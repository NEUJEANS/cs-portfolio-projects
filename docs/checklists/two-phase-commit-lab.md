# two-phase-commit-lab checklist

- [x] define portfolio goals: atomic commit, blocking behavior, and recovery replay in a small runnable lab
- [x] do brief research on prepare/commit/abort semantics and why durable decision logging matters
- [x] refresh the protocol flow with a short self-test note before coding
- [x] implement JSON scenario validation plus deterministic 2PC simulation
- [x] cover happy-path commit, participant veto abort, blocking coordinator crash, and recovery replay with committed scenarios
- [x] add CLI commands for validation, simulation, JSON output, and Markdown artifact export
- [x] add automated tests for validation, simulation outcomes, blocking semantics, and CLI artifact output
- [x] extend the lab beyond coordinator-only recovery with participant-side reconnect handling after missed second-phase delivery
- [x] surface reconnect recovery in the committed reports/catalog so the portfolio story stays visible on GitHub
- [x] add blocked-case termination-protocol hints plus a partial-decision-delivery crash scenario so the lab shows what peers can still ask while recovery is pending
- [x] add a 2PC-vs-saga comparison mode with committed Markdown/JSON artifacts and clear peer-visible decision snapshots for blocked-after-decision cases
- [x] simulate the peer-to-peer termination protocol end-to-end so blocked participants either resolve from decisive peers or stay visibly stuck
- [x] add a durable-ABORT crash scenario so peer termination resolution also shows the safe rollback path when a reachable peer never reached PREPARED
- [x] run at least 3 review passes and fix issues found
- [x] run tests, secret-scan, commit, push, and add a wrap-up note for the slice
