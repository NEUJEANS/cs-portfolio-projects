# crdt-orset-lab checklist

## Current slice (2026-04-18 19:41 UTC run)
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

## Previous slice (2026-04-18 19:10 UTC run)
- [x] confirm `main` is synced with `origin/main` before editing
- [x] do brief research on an accessible way to bundle linked HTML artifact galleries
- [x] do a short HTML artifact refresh and self-test note if needed
- [x] update/add checklist markdown for the gallery slice
- [x] add a small HTML gallery/index export that links the Markdown, Mermaid, SVG, and JSON sample outputs together
- [x] add snapshot JSON export support so the gallery can link to raw machine-readable state
- [x] commit the refreshed sample artifact bundle for `sample_ops.json`
- [x] add regression coverage for the new HTML/JSON export paths
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Completed slices
- [x] initial project scaffold, implementation, documentation, and sample scenario
- [x] timeline artifact exports for Markdown, Mermaid, and SVG portfolio screenshots
- [x] HTML gallery/index + JSON snapshot bundle for browser-friendly artifact navigation
- [x] OR-Set vs LWW-element-set comparison workflow with committed divergence artifacts

## Current quality checks
- [x] README explains why observed-remove semantics matter and how to run the simulator
- [x] README documents Markdown / Mermaid / SVG / HTML / JSON export flags and the new `compare-script` workflow
- [x] tests cover add/remove/merge behavior, convergence, script loading, CLI flows, timeline exports, comparison exports, and the diverging LWW scenario
- [x] project is resumable through the sample scripts, checklist, research/learning notes, and review/wrap-up docs

## Next follow-up ideas
- [ ] add delta-state/digest views to explain merge payload size and anti-entropy costs
- [ ] add canned comparison presets that emit multiple OR-Set vs LWW scenarios at once
- [ ] add another CRDT contrast page such as OR-Set vs MV-register or PN-counter trade-offs
