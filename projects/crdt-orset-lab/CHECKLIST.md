# crdt-orset-lab checklist

## Current slice (2026-04-18 17:52 UTC run)
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

## Current quality checks
- [x] README explains why observed-remove semantics matter and how to run the simulator
- [x] README documents timeline export flags and points to committed sample artifacts
- [x] tests cover add/remove/merge behavior, convergence, script loading, CLI flows, and timeline export generation
- [x] project is resumable through the sample script, checklist, research/learning notes, and review/wrap-up docs

## Next follow-up ideas
- [ ] add delta-state/digest views to explain merge payload size and anti-entropy costs
- [ ] compare OR-Set behavior with an LWW-element-set on the same scripted scenario
- [ ] add a small HTML gallery/index page that links the Markdown, Mermaid, SVG, and raw JSON sample outputs together
