# Graph routing negative-cycle lab wrap-up — 2026-04-19T21:17:21Z

- Project: `graph-routing-negative-cycle-lab`
- Feature commit: `9dd36cf` (`Add graph routing route diff reports`)

## What changed
- added first-class route-table comparison support so two graph variants from the same Bellman-Ford source can be compared side by side
- added `RouteTableEntry`, `EdgeChange`, `RouteDiff`, and `RoutingComparison` data models plus compare/pretty/JSON/Markdown export flows
- wired new CLI flags: `--compare-graph` and `--export-compare-markdown`
- added `route_shift_graph.json` as a checked-in comparison fixture and committed the generated Markdown artifact at `docs/artifacts/graph-routing-negative-cycle-route-diff-report.md`
- refreshed the project README/checklist and added slice research/review notes
- fixed a review-found readability bug so old/new path summaries now render as explicit bracketed transitions (`[old path] => [new path]`)
- added regression coverage for node-presence changes and the CLI guard requiring `--compare-graph` for compare-only Markdown export

## Tests and validation run
- `python3 -m py_compile projects/graph-routing-negative-cycle-lab/graph_routing_lab.py`
- `python3 -m unittest tests.test_graph_routing_negative_cycle_lab` (`27/27`)
- real Markdown artifact generation smoke:
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/route_shift_graph.json --export-compare-markdown docs/artifacts/graph-routing-negative-cycle-route-diff-report.md`
- real JSON comparison smoke with payload assertion:
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/route_shift_graph.json --format json`
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (clean)

## Review passes
- `docs/reviews/2026-04-19-graph-routing-route-diff-review.md` (3 passes)

## Next step
- build a small HTML diff dashboard or SVG summary card on top of the new Markdown route-table comparison flow so the project has a more visual portfolio artifact.
