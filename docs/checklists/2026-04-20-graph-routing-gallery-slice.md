# graph-routing-negative-cycle-lab gallery slice

- [x] confirm repo branch/remote status, fetch, and verify local `main` matches `origin/main` before editing
- [x] continue the unfinished graph-routing gallery slice already present in the dirty working tree instead of starting a different project
- [x] do brief research on semantic/static HTML patterns for reusable gallery cards
- [x] do a short Python/static-site refresh and self-test for manifest-driven artifact bundles
- [x] add a resumable slice checklist and linked notes for this gallery milestone
- [x] implement gallery manifest loading plus Markdown/HTML landing-page exports
- [x] add at least one extra comparison scenario fixture so the gallery shows more than one route-diff story
- [x] generate and commit the linked comparison artifacts for each scenario plus the shared gallery landing page
- [x] refresh project docs/checklists/README so the gallery workflow is reproducible
- [x] complete three review passes and fix the issues found
- [x] rerun focused tests, smoke commands, deterministic artifact checks, and `git diff --check`
- [x] run a secret scan before push
- [x] commit, push, and add a timestamped wrap-up

## Review passes completed
1. **Scenario-summary semantics review** — found that negative-cycle incidents were being counted as "same-cost reroutes" whenever the path changed without a cost delta; fixed by counting reroutes only when both baseline/candidate entries stay stably reachable without status/presence churn.
2. **Duplication/consistency review** — extracted shared comparison-metric summarization so the HTML dashboard, SVG card, and gallery all use the same counts.
3. **Regression review** — added focused tests covering the new metric rules plus gallery rendering so the misleading reroute count does not come back.
