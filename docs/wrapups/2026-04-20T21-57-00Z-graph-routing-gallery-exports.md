# Graph routing negative-cycle lab gallery slice — 2026-04-20T21:57:00Z

- Project: `graph-routing-negative-cycle-lab`
- Feature commit: `a2fa38a` (`feat(graph-routing-negative-cycle-lab): add route-diff gallery exports`)

## What changed
- added manifest-driven gallery loading plus `--export-gallery-markdown` / `--export-gallery-html` so multiple route-diff scenarios can publish from one declarative bundle
- added a new `link_failure_graph.json` outage-style fixture and committed its Markdown, HTML, and SVG comparison artifacts alongside the negative-cycle incident trio
- committed shared gallery outputs at `docs/artifacts/graph-routing-negative-cycle-gallery.{md,html}` and updated the project README/checklists with the new workflow
- fixed a review-found issue where negative-cycle incidents were being counted as same-cost reroutes; comparison metrics now only count stable reachable reroutes and are shared across the gallery, HTML dashboard, and SVG summary card paths
- added research, learning/self-test, and resumable checklist notes for this slice

## Tests and validation run
- `python3 -m unittest tests/test_graph_routing_negative_cycle_lab.py -v` (`41/41`)
- gallery export smoke:
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py --gallery-manifest projects/graph-routing-negative-cycle-lab/portfolio_gallery_manifest.json --export-gallery-markdown docs/artifacts/graph-routing-negative-cycle-gallery.md --export-gallery-html docs/artifacts/graph-routing-negative-cycle-gallery.html`
- deterministic route-diff artifact reruns:
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/route_shift_graph.json --export-compare-markdown docs/artifacts/graph-routing-negative-cycle-route-diff-report.md --export-compare-html docs/artifacts/graph-routing-negative-cycle-route-diff-dashboard.html --export-compare-svg docs/artifacts/graph-routing-negative-cycle-route-diff-card.svg`
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/negative_cycle_graph.json --export-compare-markdown docs/artifacts/graph-routing-negative-cycle-incident-report.md --export-compare-html docs/artifacts/graph-routing-negative-cycle-incident-dashboard.html --export-compare-svg docs/artifacts/graph-routing-negative-cycle-incident-card.svg`
  - `python3 projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/sample_graph.json --source A --mode bellman-ford --compare-graph projects/graph-routing-negative-cycle-lab/link_failure_graph.json --export-compare-markdown docs/artifacts/graph-routing-negative-cycle-link-failure-report.md --export-compare-html docs/artifacts/graph-routing-negative-cycle-link-failure-dashboard.html --export-compare-svg docs/artifacts/graph-routing-negative-cycle-link-failure-card.svg`
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (clean)

## Reviews run
- three-pass review log captured in `docs/checklists/2026-04-20-graph-routing-gallery-slice.md`

## Next step
- add gallery-level filtering or preset manifests so recruiters can pivot between reroute, outage, and negative-cycle stories without editing JSON by hand
