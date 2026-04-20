# Two-phase commit lab learning — 2026-04-20 — catalog cross-links

## Quick refresh
- The existing naming pattern was already strong enough to infer related artifacts: `<scenario>_report.md`, `<scenario>_protocol_compare.md`, `<scenario>_protocol_compare.html`, and `<scenario>_termination.md`.
- A catalog landing page becomes much more useful when it links horizontally across related artifacts instead of only vertically into the base report.
- Convention-based discovery keeps the slice resumable: future runs can add new companion files without editing scenario metadata.

## Self-test
- Q: Why detect companions by filename instead of adding per-scenario manifest JSON?
  - A: The repo already has stable deterministic filenames, so a manifest would add maintenance overhead without improving correctness for this slice.
- Q: What should the catalog do when a scenario has no comparison or termination artifact yet?
  - A: Show `-` in the table and omit those snapshot links instead of generating dead links.
- Q: Why include links in both the table and the snapshot section?
  - A: The table supports fast scanning, while the snapshot section supports deeper recruiter browsing without hunting through filenames.
