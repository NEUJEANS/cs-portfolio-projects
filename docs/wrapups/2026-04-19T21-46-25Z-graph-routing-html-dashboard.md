# Graph routing negative-cycle lab wrap-up — 2026-04-19T21:46:25Z

- Project: `graph-routing-negative-cycle-lab`
- Feature commit: `f78a0e4` (`Add graph routing HTML diff dashboard`)

## What changed
- added `--export-compare-html` so route-table diffs can be exported as a static HTML dashboard with summary cards plus detailed audit tables
- committed the sample dashboard artifact at `docs/artifacts/graph-routing-negative-cycle-route-diff-dashboard.html`
- refreshed the project README and main checklist for the new visual comparison milestone
- added focused HTML export/CLI regression coverage and a dedicated slice checklist + review log
- fixed three review-found issues before publish: removed non-deterministic timestamps from the committed artifact, corrected HTML terminology from inaccurate "next hop" wording to Bellman-Ford `predecessor`, and formatted zero cost deltas as `unchanged` for same-cost reroutes

## Tests and validation run
- deterministic re-export check: exported the HTML dashboard twice to temp files and confirmed identical SHA-256 hashes
- `python3 -m py_compile projects/graph-routing-negative-cycle-lab/graph_routing_lab.py`
- `python3 -m unittest tests.test_graph_routing_negative_cycle_lab` (`30/30`)
- real HTML export smoke:
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/route_shift_graph.json --export-compare-html docs/artifacts/graph-routing-negative-cycle-route-diff-dashboard.html`
- real JSON compare smoke with assertions:
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/route_shift_graph.json --export-compare-markdown docs/artifacts/graph-routing-negative-cycle-route-diff-report.md --format json`
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (clean)

## Reviews run
- `docs/reviews/2026-04-19-graph-routing-html-dashboard-review.md` (3 passes)

## Next step
- add a compact SVG summary card so the project has both a screenshot-friendly HTML dashboard and a single-image artifact for slide decks or README thumbnails.
