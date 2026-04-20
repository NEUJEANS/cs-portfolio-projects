# Graph routing route-diff gallery

Static landing page for three Bellman-Ford route-diff stories: same-cost path churn, a candidate negative-cycle incident, and a link-failure reachability regression.

## Gallery summary
| metric | value |
| --- | --- |
| scenario count | 3 |
| total changed routes | 9 |
| scenarios with candidate negative cycles | 1 |
| scenarios featuring same-cost reroutes | 1 |

## Scenario overview
| Scenario | Source | Story | Changed edges | Changed routes | Linked artifacts |
| --- | --- | --- | ---: | ---: | --- |
| [Same-cost reroute after edge-weight shift](#same-cost-reroute) | A | same-cost reroutes with path churn | 2 | 2 | [Markdown report](graph-routing-negative-cycle-route-diff-report.md), [HTML dashboard](graph-routing-negative-cycle-route-diff-dashboard.html), [SVG summary card](graph-routing-negative-cycle-route-diff-card.svg) |
| [Candidate negative-cycle incident](#negative-cycle-incident) | A | candidate introduces a reachable negative cycle | 8 | 4 | [Markdown report](graph-routing-negative-cycle-incident-report.md), [HTML dashboard](graph-routing-negative-cycle-incident-dashboard.html), [SVG summary card](graph-routing-negative-cycle-incident-card.svg) |
| [Link-failure reachability regression](#link-failure-regression) | A | reachability or route status changes | 4 | 3 | [Markdown report](graph-routing-negative-cycle-link-failure-report.md), [HTML dashboard](graph-routing-negative-cycle-link-failure-dashboard.html), [SVG summary card](graph-routing-negative-cycle-link-failure-card.svg) |

## Scenario cards

<a id="same-cost-reroute"></a>
### Same-cost reroute after edge-weight shift
Small weight changes flip B to a direct route and reroute D at the same final cost, showing why distance deltas alone can hide path churn.

- Source: `A`
- Baseline graph: `routing_demo`
- Candidate graph: `routing_shift_demo`
- Story label: same-cost reroutes with path churn
- Changed edges: 2
- Changed route entries: 2
- Same-cost reroutes: 1
- Cost-changing routes: 1
- Predecessor changes: 2
- Status changes: 0
- Baseline negative cycle: none
- Candidate negative cycle: none
- Changed nodes preview: B, D

#### Linked artifacts
- [Markdown report](graph-routing-negative-cycle-route-diff-report.md) — Text diff with changed edges and per-node route explanations.
- [HTML dashboard](graph-routing-negative-cycle-route-diff-dashboard.html) — Static dashboard with summary cards and audit tables.
- [SVG summary card](graph-routing-negative-cycle-route-diff-card.svg) — Compact visual card for README thumbnails or slides.

<a id="negative-cycle-incident"></a>
### Candidate negative-cycle incident
The candidate graph introduces a reachable negative cycle, turning every formerly stable route into an unstable routing incident that must be surfaced immediately.

- Source: `A`
- Baseline graph: `routing_demo`
- Candidate graph: `negative_cycle_demo`
- Story label: candidate introduces a reachable negative cycle
- Changed edges: 8
- Changed route entries: 4
- Same-cost reroutes: 0
- Cost-changing routes: 3
- Predecessor changes: 4
- Status changes: 4
- Baseline negative cycle: none
- Candidate negative cycle: A -> B -> C -> A
- Changed nodes preview: A, B, C, D

#### Linked artifacts
- [Markdown report](graph-routing-negative-cycle-incident-report.md) — Route-diff report that highlights the reachable cycle and unstable route table.
- [HTML dashboard](graph-routing-negative-cycle-incident-dashboard.html) — Static incident dashboard for the negative-cycle regression.
- [SVG summary card](graph-routing-negative-cycle-incident-card.svg) — Compact cycle-incident card for quick portfolio previews.

<a id="link-failure-regression"></a>
### Link-failure reachability regression
A broken path to D and higher route costs for B/C show how topology drift can mix cost regressions with a hard reachability failure.

- Source: `A`
- Baseline graph: `routing_demo`
- Candidate graph: `link_failure_demo`
- Story label: reachability or route status changes
- Changed edges: 4
- Changed route entries: 3
- Same-cost reroutes: 0
- Cost-changing routes: 3
- Predecessor changes: 2
- Status changes: 1
- Baseline negative cycle: none
- Candidate negative cycle: none
- Changed nodes preview: B, C, D

#### Linked artifacts
- [Markdown report](graph-routing-negative-cycle-link-failure-report.md) — Diff artifact for the partial outage / unreachable-destination scenario.
- [HTML dashboard](graph-routing-negative-cycle-link-failure-dashboard.html) — Static dashboard covering the link-failure regression.
- [SVG summary card](graph-routing-negative-cycle-link-failure-card.svg) — Compact outage card showing the reachability regression.
