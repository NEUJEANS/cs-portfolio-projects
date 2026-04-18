# crdt-orset-lab checklist

## Current slice (2026-04-18 20:31 UTC run)
- [x] confirm `main` still matches `origin/main` before editing and preserve the already-finished anti-entropy/checklist diff
- [x] do only the brief HTML replay / accessibility research needed for the scrubber and announcement behavior
- [x] do a short Python/CLI self-test refresh for replay-output wiring
- [x] update/add checklist markdown for the replay slice
- [x] add a first-class replay/animation HTML export that scrubs replica state alongside the anti-entropy transfer table
- [x] generate and commit replay artifact bundles for the baseline OR-Set sample and the OR-Set side of the comparison scenario
- [x] update README usage, committed artifact examples, and future follow-up notes
- [x] extend regression coverage for replay-frame construction, replay HTML rendering, and CLI replay export wiring
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Previous slice (2026-04-18 20:11 UTC run)
- [x] confirm `main` still matches `origin/main` before editing and preserve the local anti-entropy diff
- [x] do only the brief CRDT anti-entropy/delta-state refresh needed for wording and scope
- [x] do a short Python/CLI self-test refresh for digest/delta export paths
- [x] update/add checklist markdown for the anti-entropy slice
- [x] finish the digest + delta-state reporting flow and expose anti-entropy Markdown/HTML/JSON outputs from the CLI
- [x] generate and commit anti-entropy artifact bundles for the baseline OR-Set sample and the OR-Set side of the comparison scenario
- [x] update README usage, artifact examples, and future follow-up notes
- [x] extend regression coverage for anti-entropy summaries and CLI export wiring
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Earlier slice (2026-04-18 19:41 UTC run)
- [x] confirm `main` is synced with `origin/main` before editing
- [x] inspect and preserve the pre-existing local in-progress `crdt_orset_lab.py` comparison diff instead of overwriting it
- [x] do brief semantics verification only as needed for OR-Set vs LWW comparison wording
- [x] do a short Python/CLI self-test refresh for the new comparison path
- [x] update/add checklist markdown for the comparison slice
- [x] finish the `compare-script` CLI flow and make comparison Markdown/HTML/JSON outputs first-class
- [x] add a committed timestamped comparison scenario that makes OR-Set and LWW diverge on final membership
- [x] regenerate and commit the comparison artifact bundle under `docs/artifacts/crdt-orset-lab/`
- [x] extend regression coverage for LWW state handling and `compare-script` outputs
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Completed slices
- [x] initial project scaffold, implementation, documentation, and sample scenario
- [x] timeline artifact exports for Markdown, Mermaid, and SVG portfolio screenshots
- [x] HTML gallery/index + JSON snapshot bundle for browser-friendly artifact navigation
- [x] OR-Set vs LWW-element-set comparison workflow with committed divergence artifacts
- [x] digest + delta-state anti-entropy reports for baseline and comparison-linked OR-Set scenarios
- [x] replay/animation HTML exports that pair the state timeline with anti-entropy transfer details

## Current quality checks
- [x] README explains why observed-remove semantics matter and how to run the simulator
- [x] README documents Markdown / Mermaid / SVG / HTML / JSON export flags, the anti-entropy report outputs, the replay page, and the `compare-script` workflow
- [x] tests cover add/remove/merge behavior, convergence, script loading, CLI flows, timeline exports, replay exports, anti-entropy exports, comparison exports, and the diverging LWW scenario
- [x] project is resumable through the sample scripts, checklist, research/learning notes, and review/wrap-up docs

## Next follow-up ideas
- [ ] add canned comparison presets that emit multiple OR-Set vs LWW scenarios at once
- [ ] add another CRDT contrast page such as OR-Set vs MV-register or PN-counter trade-offs
- [ ] add jump-to-sync or playback-speed controls so classroom demos can skip directly to the expensive reconciliation steps
