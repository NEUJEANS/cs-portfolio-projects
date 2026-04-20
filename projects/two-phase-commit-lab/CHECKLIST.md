# two-phase-commit-lab checklist

## Completed slices
- [x] Create an initial distributed-transaction portfolio lab with scenario validation, deterministic 2PC simulation, Markdown report export, and committed sample scenarios
- [x] Add a multi-scenario catalog command and committed landing-page artifact bundle for recruiter-friendly browsing
- [x] Model participant reconnect recovery after missed second-phase messages and surface the behavior in the catalog/report artifacts
- [x] Add participant-to-participant termination-protocol hints for coordinator-unavailable blocked cases, including a partial-decision-delivery crash scenario
- [x] Add a 2PC-vs-saga comparison mode with committed Markdown/JSON artifacts, plus peer-visible decision snapshots for the partial-delivery blocked case

## Next candidate slices
- [ ] add scenario tags or thematic grouping controls if the sample set grows beyond the current six cases
- [ ] optionally simulate full peer-to-peer termination resolution once a blocked participant reaches a decisive peer
- [ ] consider a compact HTML comparison dashboard if the protocol-comparison artifact set grows beyond Markdown/JSON
