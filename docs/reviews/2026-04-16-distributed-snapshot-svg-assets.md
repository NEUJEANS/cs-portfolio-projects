# Distributed Snapshot Lab Review Log — 2026-04-16 — SVG Assets Slice

## Review pass 1 — export workflow reproducibility
- Re-ran the walkthrough generator with both `--output` and `--svg-dir`, then diffed stdout against the written Markdown artifact.
- Found a documentation gap: the README example still showed only Markdown export, so the committed SVG asset workflow was not reproducible from the project docs.
- Fix applied: updated the README feature list, walkthrough example, shipped-artifact note, and output notes to document `--svg-dir`/`--svg-prefix` and the committed SVG asset directory.

## Review pass 2 — asset-linking edge case audit
- Re-ran `python3 -m unittest discover -s projects/distributed-snapshot-lab -p 'test_*.py' -v` and inspected the walkthrough/SVG helper flow.
- Found an edge-case bug: walkthrough asset lookup used the display-sanitized snapshot label instead of the raw snapshot ID, which could break asset linking for IDs containing quotes.
- Fix applied: keyed asset lookup by the raw snapshot ID, kept the sanitized version only for display, and added a regression test that uses a quoted snapshot ID while still expecting the SVG asset link to render.

## Review pass 3 — checklist/future-slice honesty audit
- Reviewed the project checklist, generated artifact, and README future-improvement section after the export changes landed.
- Found a bookkeeping mismatch: the checklist still treated `SVG/PNG` as one unfinished item even though this slice completes SVG export but intentionally leaves PNG for later.
- Fix applied: checked off the SVG slice explicitly, split PNG into its own remaining follow-up item, and added a dedicated slice checklist/research/refresh trail for resumability.
