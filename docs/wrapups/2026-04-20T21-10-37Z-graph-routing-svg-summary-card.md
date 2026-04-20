# Graph routing negative-cycle lab SVG summary card slice — 2026-04-20T21:10:37Z

- Project: `graph-routing-negative-cycle-lab`
- Feature commit: `2a1171a` (`feat(graph-routing-negative-cycle-lab): add svg route diff card`)

## What changed
- added a deterministic `--export-compare-svg` flow plus `render_svg_comparison()` so route-table diffs can be exported as a compact slide-ready/README-ready SVG card
- committed the sample SVG artifact at `docs/artifacts/graph-routing-negative-cycle-route-diff-card.svg`
- refreshed the project README and main checklist for the new visual comparison milestone
- added slice notes for checklist, research, learning/self-test, and a 3-pass review log
- fixed two review-found issues before publish: corrected the SVG height calculation so cards/footers stay inside the `viewBox`, and added explicit `preserveAspectRatio` plus an edge-preview truncation note for safer thumbnail scaling

## Tests and validation run
- `python3 -m py_compile projects/graph-routing-negative-cycle-lab/graph_routing_lab.py tests/test_graph_routing_negative_cycle_lab.py`
- `python3 -m unittest tests.test_graph_routing_negative_cycle_lab -v` (`33/33`)
- SVG-focused reruns after review fixes:
  - `python3 -m unittest tests.test_graph_routing_negative_cycle_lab.GraphRoutingNegativeCycleLabTests.test_export_compare_svg_writes_summary_card tests.test_graph_routing_negative_cycle_lab.GraphRoutingNegativeCycleLabTests.test_cli_can_export_compare_svg -v`
- real artifact-generation smoke:
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/route_shift_graph.json --export-compare-markdown docs/artifacts/graph-routing-negative-cycle-route-diff-report.md --export-compare-html docs/artifacts/graph-routing-negative-cycle-route-diff-dashboard.html --export-compare-svg docs/artifacts/graph-routing-negative-cycle-route-diff-card.svg`
- deterministic SVG re-export check via repeated SHA-256 comparison (matching hashes)
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (clean)

## Reviews run
- `docs/reviews/2026-04-20-graph-routing-svg-summary-card-review.md` (3 passes)

## Next step
- add a small multi-scenario routing gallery page so several graph diff fixtures can share one portfolio landing page with linked Markdown, HTML, and SVG comparison artifacts
