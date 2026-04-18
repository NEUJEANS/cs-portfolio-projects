# crdt-orset-lab checklist

## Current slice (2026-04-18 22:15 UTC run)
- [x] confirm `main` still matches `origin/main` before editing
- [x] do only the brief preset-pattern/tooling refresh needed to mirror the repo's existing built-in-preset style
- [x] keep the slice narrow: add resumable built-in OR-Set vs LWW comparison presets plus one summary-suite command
- [x] update/add checklist markdown for the comparison-preset suite slice
- [x] add built-in comparison preset metadata and a `list-presets` / `compare-presets` CLI flow
- [x] add committed preset scripts for an unobserved-remove divergence case and an observed-remove control case
- [x] generate and commit the preset-suite summary artifacts under `docs/artifacts/crdt-orset-lab/`
- [x] update README usage, committed artifact examples, and future follow-up notes
- [x] extend regression coverage for preset listing, suite summaries, and suite artifact writing
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan
- [x] commit, push, and write the wrap-up

## Previous slice (2026-04-18 21:13 UTC run)
- [x] confirm `main` still matches `origin/main` before editing
- [x] do the brief hash-link / fragment-routing research needed for deep-linkable replay checkpoints
- [x] do a short Python/CLI self-test refresh for replay hash parsing and canonical-link rendering
- [x] update/add checklist markdown for the deep-link slice
- [x] add hash-based replay links so the generated HTML can open directly on `#step-N` or `#sync-N`
- [x] surface the current canonical link plus all sync checkpoint links inside the replay artifact itself
- [x] regenerate updated replay artifacts for the baseline OR-Set sample and comparison scenario
- [x] update README usage, committed artifact examples, and future follow-up notes
- [x] extend regression coverage for replay-frame sync checkpoint metadata and deep-link rendering
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan
- [x] commit, push, and write the wrap-up

## Current slice (2026-04-18 21:41 UTC run)
- [x] confirm `main` still matches `origin/main` before editing
- [x] do the brief clipboard / blob-download research needed for replay checkpoint share/export actions
- [x] do a short JavaScript/browser self-test refresh for copy-link fallback and generated SVG download wiring
- [x] update/add checklist markdown for the replay export-affordances slice
- [x] add copy-link actions for the exact replay frame and stable sync checkpoints inside the replay artifact
- [x] add standalone checkpoint SVG export so the current replay state can be downloaded directly from the browser
- [x] regenerate updated replay artifacts for the baseline OR-Set sample and comparison scenario
- [x] update README usage, committed artifact examples, and future follow-up notes
- [x] extend regression coverage for replay action controls and checkpoint-SVG export wiring
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan
- [x] commit, push, and write the wrap-up

## Previous slice (2026-04-18 21:04 UTC run)
- [x] confirm `main` still matches `origin/main` before editing
- [x] do only the brief replay-control accessibility refresh needed for jump/playback controls
- [x] do a short Python/CLI self-test refresh for replay-control wiring
- [x] update/add checklist markdown for the replay-controls slice
- [x] add jump-to-sync and playback-speed controls to the replay HTML so demos can skip directly to reconciliation steps
- [x] regenerate and commit updated replay artifacts for the baseline OR-Set sample and comparison scenario
- [x] update README usage, committed artifact examples, and future follow-up notes
- [x] extend regression coverage for replay-control rendering and sync-step navigation metadata
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Previous slice (2026-04-18 20:31 UTC run)
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
- [x] replay controls that jump directly between sync checkpoints and adjust playback speed for demos
- [x] built-in OR-Set vs LWW comparison presets plus a summary-suite command/artifact bundle

## Current quality checks
- [x] README explains why observed-remove semantics matter and how to run the simulator
- [x] README documents Markdown / Mermaid / SVG / HTML / JSON export flags, the anti-entropy report outputs, the replay page, the `compare-script` workflow, and the new preset-suite commands
- [x] tests cover add/remove/merge behavior, convergence, script loading, CLI flows, timeline exports, replay exports, anti-entropy exports, comparison exports, preset listing, and the preset-suite summaries
- [x] project is resumable through the sample scripts, checklist, research/learning notes, and review/wrap-up docs

## Next follow-up ideas
- [ ] add per-preset detail export bundles so the preset suite can link directly to timeline/replay/anti-entropy pages for each scenario
- [ ] add another CRDT contrast page such as OR-Set vs MV-register or PN-counter trade-offs
- [ ] add PNG/export bundling on top of the replay checkpoint SVG downloads for slide decks that need bitmap assets
