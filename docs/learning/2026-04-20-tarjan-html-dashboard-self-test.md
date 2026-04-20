# Tarjan SCC HTML dashboard self-test — 2026-04-20

- Goal: keep the next slice small and portfolio-friendly by reusing the existing `compare` payload instead of inventing a new benchmark schema.
- Refresher: static HTML artifacts work best here when they are self-contained, use inline CSS, and compute sibling artifact links relative to the HTML output path.
- Refresher: direct `--json-output` is cleaner than shell redirection when one command needs to emit JSON, CSV, Markdown, and HTML as one resumable artifact bundle.
- Self-check plan:
  - render trial-level timing cards from the same per-run rows already used for CSV output
  - render component cards from `comparison["components"]` without recomputing SCC structure
  - keep HTML link generation path-aware so checked-in artifacts remain portable inside `docs/artifacts/`
