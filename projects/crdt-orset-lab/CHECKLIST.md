# crdt-orset-lab checklist

## Current slice (2026-04-18 17:25 UTC run)
- [x] confirm `main` is synced with `origin/main` before editing
- [x] do brief CRDT/OR-Set research and record the scope for this slice
- [x] do a short Python/distributed-systems refresh with a self-test note
- [x] create a new OR-Set portfolio project with replica-local tags, observed-remove semantics, merge logic, and a scriptable cluster simulator
- [x] add README usage/storytelling plus a committed sample scenario
- [x] add regression coverage for merge properties, convergence, script loading, and CLI flows
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Completed slices
- [x] initial project scaffold, implementation, documentation, and sample scenario

## Current quality checks
- [x] README explains why observed-remove semantics matter and how to run the simulator
- [x] tests cover add/remove/merge behavior, convergence, input validation, and CLI flows
- [x] project is resumable through the sample script, checklist, and review/wrap-up notes

## Next follow-up ideas
- [ ] add Mermaid or SVG timeline exports for portfolio screenshots
- [ ] add delta-state/digest views to explain merge payload size and anti-entropy costs
- [ ] compare OR-Set behavior with an LWW-element-set on the same scripted scenario
