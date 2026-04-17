# Review pass 2 — docs/checklist alignment

- Scope: `projects/network-flow-lab/README.md`, `projects/network-flow-lab/CHECKLIST.md`, `docs/checklists/network-flow-lab.md`, and `docs/artifacts/network-flow-lab/index.md`
- Checks: usage examples, committed-artifact references, future-ideas drift, and resumable checklist state.
- Issue found: the new benchmark HTML gallery needed to be surfaced everywhere a reviewer would look first, otherwise the slice would be implemented but easy to miss.
- Fix applied: added the new `benchmark-gallery-demo` feature/usage/docs references, linked `benchmark-gallery.html` from the artifact index, and marked the checklist slice complete in both project-local and docs-level checklists.
- Result after fix: README + artifact index + checklist state now point to the same deliverable and the next run can resume cleanly.
