# Two-phase commit lab research — 2026-04-20 — HTML comparison dashboard

## Why no external web research this slice
- This slice only changes artifact presentation around an already-implemented and already-reviewed 2PC-vs-saga comparison model.
- No protocol semantics changed, so fresh external research was not necessary for correctness.

## Internal references reviewed
- `projects/graph-routing-negative-cycle-lab/graph_routing_lab.py`
  - static comparison-dashboard layout patterns for summary cards, detail panels, and deterministic artifact output
- `projects/regex-engine-lab/regex_engine_lab.py`
  - lightweight dashboard styling and no-JS artifact structure suitable for committed portfolio HTML files

## Slice decision
- Keep the HTML output deterministic, dependency-free, and static so it can be committed directly, rendered on GitHub Pages, and regenerated in tests without browser-only tooling.
