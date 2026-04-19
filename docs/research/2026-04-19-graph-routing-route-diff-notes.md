# 2026-04-19 research notes — graph-routing route diff slice

## Question
What details make a route-table comparison artifact feel realistic instead of just printing two shortest-path runs side by side?

## Brief takeaway
A useful routing diff should highlight:
- **metric / cost changes** because the preferred path can change even when reachability does not
- **next-hop / predecessor changes** because operators often care which hop changed, not just the final total
- **reachability / instability changes** because negative cycles or lost connectivity matter more than tiny cost shifts

## Applied to this slice
That pushed the implementation toward a comparison report with:
- explicit edge-weight change rows
- per-node predecessor and path deltas
- same-cost path-change summaries so alternate-route swaps still stand out
- negative-cycle summaries for both sides of the comparison

## Sources used
- FRRouting dev guide, **Next Hop Tracking** — useful reminder that next-hop reachability/validity directly affects route usefulness, so the diff output should call out reachability/status changes and not only path cost changes.
  - https://docs.frrouting.org/projects/dev-guide/en/latest/next-hop-tracking.html
- ipSpace blog, **Routing Protocol Metrics** — useful refresher that path choice depends on comparable metrics/costs, which justified explicit cost-delta rows in the report.
  - https://blog.ipspace.net/2024/01/routing-protocol-metrics/
- brief web search on routing-table diff metrics, next-hop reachability, and shortest-path comparison concepts
- existing in-repo project context for Bellman-Ford, Johnson, and negative-cycle reporting
