# 2026-04-16 Karger Graphviz refresh and self-test

## Quick refresh
- Graphviz DOT uses an undirected `graph` with `--` edges for this project.
- Each contraction step can be rendered as one node per surviving supernode.
- Parallel edges should not be collapsed away; instead, aggregate multiplicity and surface it with an edge label and thicker pen width.
- A useful resumable export pattern is `step-00.dot`, `step-01.dot`, ... so later slices can batch-render or animate them.

## Self-test
- How do we show a merged supernode clearly? Use a node label that lists member vertices on separate lines.
- How do we keep the initial graph renderable? Seed step 0 from the original input edges and singleton supernodes.
- What extra trace data is needed beyond just the picked edge? Remaining supernodes plus remaining multiedges after each contraction.
- How should CLI behavior work when DOT export is requested? Automatically force trace capture, then return the written file paths in JSON output.
