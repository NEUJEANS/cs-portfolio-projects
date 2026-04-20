# two-phase-commit-lab checklist

## Completed slices
- [x] Create an initial distributed-transaction portfolio lab with scenario validation, deterministic 2PC simulation, Markdown report export, and committed sample scenarios
- [x] Add a multi-scenario catalog command and committed landing-page artifact bundle for recruiter-friendly browsing
- [x] Model participant reconnect recovery after missed second-phase messages and surface the behavior in the catalog/report artifacts
- [x] Add participant-to-participant termination-protocol hints for coordinator-unavailable blocked cases, including a partial-decision-delivery crash scenario
- [x] Add a 2PC-vs-saga comparison mode with committed Markdown/JSON artifacts, plus peer-visible decision snapshots for the partial-delivery blocked case
- [x] Simulate full peer-to-peer termination resolution for blocked runs, including one scenario that resolves via an informed peer and one that still stays blocked
- [x] Add a blocked-after-ABORT sample so peer termination resolution demonstrates both decisive COMMIT witnesses and safe ABORT proofs via a non-prepared peer
- [x] Add a compact static HTML dashboard for protocol comparison artifacts so recruiters can browse 2PC-vs-saga tradeoffs without reading Markdown first
- [x] Cross-link the scenario catalog to committed comparison dashboards and peer-termination walkthrough artifacts when those companions exist

## Next candidate slices
- [ ] add scenario tags or thematic grouping controls if the sample set grows beyond the current seven cases
- [ ] add a sequence-diagram or timeline export for the termination-resolution flow
- [ ] add a compact incident-response landing page that groups blocked scenarios by recovery, peer-visible COMMIT, and safe-ABORT evidence
