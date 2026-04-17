# Mini MapReduce docs index slice (2026-04-17 19:06 UTC run)

- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the previous wrap-up already scoped the docs-index follow-up clearly
- [x] do a short Python `Path` / relative-link refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a `docs-index` landing-page flow that links plugin catalogs, plugin docs, inspection diffs, benchmark reports, and annotation-batch manifests
- [x] generate committed Mini MapReduce docs artifacts for the plugin catalog, per-plugin pages, diff bundle, project-week benchmark bundle, and docs index
- [x] extend project-level and repo-level tests for real docs-index discovery and CLI output
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Review notes
- review pass 1: fixed docs drift in `projects/mini-mapreduce-lab/CHECKLIST.md` and `README.md`, and fixed the Markdown docs index so annotation-batch browser links include the preset name instead of showing two identical labels.
- review pass 2: generated the real artifact bundle under `docs/artifacts/mini-mapreduce/`, then reverted accidental timing-only churn in the older annotation-batch artifacts so the slice stays surgical.
- review pass 3: reran `py_compile` + both unittest entrypoints and added a link audit that verifies every docs-index JSON/README link resolves to a real committed file.
