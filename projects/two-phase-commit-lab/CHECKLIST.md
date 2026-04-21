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
- [x] Add a compact incident-response landing page that groups blocked scenarios by recovery, peer-visible COMMIT, and safe-ABORT evidence
- [x] Add standalone SVG/HTML timeline exports for blocked peer-termination walkthroughs and surface those visuals in the catalog/dashboard artifacts
- [x] Add reusable scenario tags plus catalog theme-group sections so the sample bundle is easier to browse by blocking/recovery/reconnect story
- [x] Add tag-filtered catalog generation plus a committed peer-assisted subset bundle so recruiters can browse a smaller scenario pack without hand-curating file lists
- [x] Add saved named bundle presets on top of the tag-filtered catalog flow so common walkthrough bundles are one flag away
- [x] Extend protocol comparison artifacts from 2PC-vs-saga to 2PC-vs-3PC-vs-saga so the lab explains why timeout-assisted atomic commit is still mostly a teaching protocol
- [x] Add PNG/social-preview export for peer-termination timeline artifacts so blocked-case visuals are easy to reuse in README hero images or slide decks

## Next candidate slices
- [ ] add a compact cross-scenario gallery page that shows the blocked timeline PNG covers beside links to the full SVG/HTML walkthroughs
