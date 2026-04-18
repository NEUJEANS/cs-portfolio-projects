# crdt-orset-lab checklist

## Current slice (2026-04-18 19:10 UTC run)
- [x] confirm `main` is synced with `origin/main` before editing
- [x] do brief research on an accessible way to bundle linked HTML artifact galleries
- [x] do a short HTML artifact refresh and self-test note if needed
- [x] update/add checklist markdown for the gallery slice
- [x] add a small HTML gallery/index export that links the Markdown, Mermaid, SVG, and JSON sample outputs together
- [x] add snapshot JSON export support so the gallery can link to raw machine-readable state
- [x] commit the refreshed sample artifact bundle for `sample_ops.json`
- [x] add regression coverage for the new HTML/JSON export paths
- [x] run targeted tests, smoke checks, and 3 review passes
- [ ] run secret scan, commit, push, and write the wrap-up

## Previous slice (2026-04-18 17:52 UTC run)
- [x] confirm `main` is synced with `origin/main` before editing
- [x] do brief research on how to make the OR-Set scenario visualization-friendly
- [x] do a short Mermaid/SVG refresh and self-test note
- [x] update/add checklist markdown for the visualization slice
- [x] add optional timeline exports for Markdown, Mermaid, and SVG output
- [x] commit a sample artifact bundle for `sample_ops.json`
- [x] add regression coverage for the new renderers and CLI export paths
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Completed slices
- [x] initial project scaffold, implementation, documentation, and sample scenario
- [x] timeline artifact exports for Markdown, Mermaid, and SVG portfolio screenshots
- [x] HTML gallery/index + JSON snapshot bundle for browser-friendly artifact navigation

## Current quality checks
- [x] README explains why observed-remove semantics matter and how to run the simulator
- [x] README documents Markdown / Mermaid / SVG / HTML / JSON export flags and points to committed sample artifacts
- [x] tests cover add/remove/merge behavior, convergence, script loading, CLI flows, and timeline/HTML/JSON export generation
- [x] project is resumable through the sample script, checklist, research/learning notes, and review/wrap-up docs

## Next follow-up ideas
- [ ] add delta-state/digest views to explain merge payload size and anti-entropy costs
- [ ] compare OR-Set behavior with an LWW-element-set on the same scripted scenario
- [ ] add a side-by-side comparison page that highlights where OR-Set and LWW diverge on concurrent add/remove histories
