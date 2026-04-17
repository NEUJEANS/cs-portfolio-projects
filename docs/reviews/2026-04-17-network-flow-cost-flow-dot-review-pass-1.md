# Network-flow generic cost-flow DOT review - pass 1

## Focus
Code-path audit for the new generic min-cost-flow DOT renderer.

## Checks run
- Reviewed the `render_min_cost_flow_dot()` implementation and the `cost-solve` / `cost-demo` CLI wiring in `projects/network-flow-lab/network_flow.py`.
- Compared the new DOT output shape against the existing flow/matching DOT exporters for label/style consistency.

## Findings
- The first draft was functionally correct, but its node ordering came from plain alphabetical sorting, which made the source/sink declarations less readable in committed artifacts.
- The DOT label and edge styling approach fit the existing portfolio-oriented artifact style.

## Fix applied
- Reordered generic cost-flow DOT node emission to place the source first, middle nodes in sorted order, and the sink last.

## Result
- The new DOT export is easier to scan and better aligned with the rest of the graph-artifact suite.
