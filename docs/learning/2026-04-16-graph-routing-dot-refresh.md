# 2026-04-16 graph-routing DOT refresh

## Quick refresh
- Graphviz DOT uses `digraph ... {}` with directed edges written as `A -> B`.
- Node and edge appearance can be controlled inline with attribute lists like `[label="...", color="..."]`.
- For this lab, a useful artifact should keep the whole graph visible while styling Bellman-Ford shortest-path edges differently from reachable negative-cycle edges.
- DOT is a good complement to Mermaid because it can plug into Graphviz-native workflows and later render to PNG/SVG without changing the algorithm output.

## Self-test
1. What is the right edge operator for a directed routing graph?
   - `->`
2. Why keep dashed styling for non-highlighted edges?
   - It preserves graph context without visually competing with the chosen shortest-path tree or negative cycle.
3. Why label nodes with distances in the artifact?
   - It makes the structural picture line up with the Bellman-Ford numeric output during demos and code review.
4. When should negative-cycle styling override shortest-path styling?
   - When an edge or node participates in the reachable cycle, because that failure mode is the most important debugging signal.

## Implementation decision
- Reuse the existing predecessor-path reconstruction and cycle-edge detection helpers.
- Export plain `.dot` text only; rendering images can remain an optional future step if Graphviz is installed.
