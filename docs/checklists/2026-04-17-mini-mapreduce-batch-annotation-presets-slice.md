# Mini MapReduce batch annotation presets slice (2026-04-17 17:57 UTC run)

- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the previous wrap-up already scoped the preset follow-up clearly
- [x] do a short Python dataclass/relative-path refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add batch benchmark preset export support that emits both full and filtered annotation views in one run
- [x] keep timing/heatmap artifacts shared across preset views so side-by-side comparisons stay stable
- [x] extend project-level and repo-level tests for manifest output and preset artifact generation
- [x] generate committed example preset-batch artifacts for the project-week plugin benchmark
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Review notes
- review pass 1: validated the new batch manifest/output flow and fixed the manifest so it records self-relative paths (`output_dir: "."`) instead of an absolute machine-specific directory.
- review pass 2: re-ran project and repo tests after the portability fix and updated coverage so both batch builders and CLI output assert the portable manifest contract.
- review pass 3: generated the committed project-week batch artifacts and rechecked that the shared CSV/heatmap files stay identical across the `full` and `portfolio-tight` views.
