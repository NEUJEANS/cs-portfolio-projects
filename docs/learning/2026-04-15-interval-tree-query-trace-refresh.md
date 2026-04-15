# Interval Tree Query Trace Refresh - 2026-04-15

## Goal
Make interval-tree pruning behavior portfolio-visible instead of only describing it in prose.

## Refresher
- Graphviz DOT is a lightweight, dependency-free interchange format that can be generated as plain text and rendered later with `dot -Tpng` or online viewers.
- For interval-tree overlap search, the most educational edges are:
  - left edge searched only when `left.max_end >= query.start`
  - right edge searched only when `node.interval.start <= query.end`
- A useful demo export should distinguish:
  - visited branches
  - pruned branches
  - nodes that actually overlap the query

## Self-test
1. Can the export show both visited and pruned branches? Yes.
2. Can it be generated without requiring Graphviz to be installed locally? Yes, DOT text only.
3. Is the output deterministic enough for tests and README examples? Yes, because node ids are assigned by stable traversal order.
