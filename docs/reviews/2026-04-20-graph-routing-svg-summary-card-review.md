# Graph routing negative-cycle lab SVG summary card review — 2026-04-20

## Pass 1 — layout geometry audit
- Reviewed the first generated SVG against the actual rendered geometry instead of just the string output.
- Issue found: the initial height calculation was too short, so the second route card and footer overflowed the `viewBox`.
- Fix applied: moved the card stack geometry to a route-section-based height calculation derived from `summary_y`, `route_y`, and the number of featured diffs.
- Validation: reran the SVG-focused unit tests, regenerated the committed SVG artifact, and confirmed the final `viewBox`/footer positioning matched the full rendered content.

## Pass 2 — scaling/accessibility audit
- Reviewed the export against the quick MDN notes for `viewBox` and SVG descriptive elements.
- Issue found: the first export relied on `viewBox` alone, which was workable but less explicit than necessary for thumbnail-style embedding, and the edge preview gave no hint if more than three edge changes existed.
- Fix applied: added `preserveAspectRatio="xMidYMin meet"` to the root SVG and appended a `+N more edge changes` note whenever the edge preview truncates a longer change list.
- Validation: extended the SVG regression expectation for `preserveAspectRatio`, reran the SVG-focused tests, and regenerated the sample artifact.

## Pass 3 — docs and smoke audit
- Reviewed the README/checklist references and regenerated the Markdown + HTML + SVG route-diff bundle together from the CLI.
- Result: no additional issues found after the first two fixes.
- Validation: reran `python3 -m unittest tests.test_graph_routing_negative_cycle_lab -v`, regenerated the committed artifacts, and reran `git diff --check`.
