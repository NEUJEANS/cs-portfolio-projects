# 2026-04-16 graph-routing Mermaid refresh

## Quick refresh
- Mermaid flowcharts are a lightweight way to ship explainable graph artifacts without adding image-generation dependencies.
- For this lab, Bellman-Ford gives a natural shortest-path tree from one source, so the artifact can highlight predecessor-derived path edges and annotate node distances.
- A reachable negative cycle should be called out separately because shortest-path semantics stop being well-defined once the cycle can keep reducing path cost.

## Self-test
1. Why not render Johnson all-pairs output in one diagram?
   - Because one graph would be cluttered and ambiguous; a single-source Bellman-Ford artifact is easier to explain in a portfolio README.
2. What should be highlighted in a negative-cycle artifact?
   - The cycle nodes/edges plus the Bellman-Ford distances that show why the graph is unstable.
3. Why reconstruct predecessor paths first instead of styling all edges?
   - Highlighting only the chosen shortest-path tree keeps the visual focused and makes the algorithm output interpretable.
