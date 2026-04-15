# Union-Find dual-axis chart slice research

## Why no external web research this run
This slice is a direct extension of the existing artifact/export workflow in `union-find-network-lab`.
The project already emits benchmark-series runs with both throughput and `stats.largest_component`, so the main work is chart design and artifact refresh rather than new algorithm research.

## Slice goal
Render a stronger portfolio artifact where a single benchmark chart shows:
- throughput (`edges_per_second`) on one axis
- resulting largest-component size on a second axis

That tells a better story than throughput alone because it connects performance to graph-growth behavior.
