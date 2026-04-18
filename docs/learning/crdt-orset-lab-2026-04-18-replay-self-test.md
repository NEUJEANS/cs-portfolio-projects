# crdt-orset-lab learning/self-test — 2026-04-18 — replay slice

## Refresh
Only a small refresh was needed: generated static HTML can still feel demo-ready if the page keeps the state model simple and reuses the same exported snapshot/timeline data instead of inventing a separate browser-only representation.

## Self-test checklist
- re-ran `py_compile` on both the implementation and test file before broader validation
- re-ran the project unittest suite after adding replay-frame helpers and replay HTML rendering
- regenerated replay bundles for both `sample_ops.json` and `sample_compare_ops.json` from the CLI rather than editing artifact HTML by hand
- opened the generated replay page through a local static HTTP server and confirmed the stepper loads, the controls render, and the first/next-step states change in a real browser
- confirmed the replay HTML links back to the timeline gallery, anti-entropy pages, and comparison page when those companion files exist

## Takeaway
For portfolio artifacts, a replay page does not need a frontend framework. A single generated HTML file plus a small JSON-backed stepper is enough—as long as the CLI remains the single source of truth for every exported view.
