# Review log — 2026-04-18 — page-replacement lab clock + presets slice

## Review pass 1 — static API/doc audit
- Checked the new Clock + preset CLI surface against the updated README and checklist docs.
- Found one polish issue: preset discovery output exposed names and pages but not workload length, which made it harder to quickly choose a demo/reference string.
- Fix applied: added `reference_length` to `list-presets --json` and added `(length=...)` to the text listing.

## Review pass 2 — real CLI smoke audit
- Re-ran real `compare`, `study`, `simulate --show-steps`, and `list-presets` flows on built-in presets.
- Found one UX issue: the README examples showed both preset-driven and explicit-page runs but did not clearly warn that `--preset` cannot be combined with `--page` or `--pages-file` in the same invocation.
- Fix applied: documented the mutual-exclusion rule directly in the README and kept the validation test for the mixed-input failure path.

## Review pass 3 — regression / packaging audit
- Re-ran `py_compile`, the project unittest suite, JSON assertions for preset metadata, and `git diff --check`.
- Verified that the final slice stays deterministic, passes all tests, and has no remaining doc/code drift in the reviewed files.
