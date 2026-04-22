# Distance Vector Failure Benchmark Research Note

- Date: 2026-04-22
- Project: `distance-vector-routing-lab`
- Slice: failure benchmark comparison

## Brief research takeaway
A quick refresher on RIP-style loop mitigation confirmed the teaching angle for this slice:
- split horizon avoids advertising a route back to the neighbor it came from
- poison reverse advertises that reverse path as unreachable instead of staying silent
- triggered updates speed propagation after topology changes, but they do not replace loop-mitigation rules on their own

## Sources checked
- Juniper RIP overview (loop mitigation and triggered update behavior)
- general RIP/count-to-infinity explainers surfaced via web search for quick terminology alignment

## Decision for this slice
Build a benchmark that compares reconvergence after link failure across routing modes and periodic vs triggered propagation, focusing on one watched route so the portfolio story stays concrete instead of abstract.
