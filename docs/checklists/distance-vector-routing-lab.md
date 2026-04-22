# Distance Vector Routing Lab Checklist

## 2026-04-15 initial build slice
- [x] brief research note captured
- [x] short refresh and self-test captured
- [x] create project scaffold and README
- [x] implement a Bellman-Ford-style distance-vector simulator with convergence rounds
- [x] add split horizon and poison reverse advertisement modes
- [x] add link-removal reconvergence support and JSON CLI output
- [x] add unit tests for steady-state routing, mitigation modes, and failure handling
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-15 diagram export slice
- [x] brief research note skipped because existing project context and networking knowledge were sufficient for this slice
- [x] short refresh and CLI self-test captured
- [x] add a resumable slice checklist entry
- [x] implement Graphviz and Mermaid export for topology and route snapshots
- [x] document diagram export usage in the project README
- [x] add unit tests for direct export helpers and CLI diagram output
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-15 count-to-infinity timeline slice
- [x] brief research note captured
- [x] short refresh and self-test captured
- [x] add a resumable slice checklist entry
- [x] make failure simulation continue from converged pre-failure routing tables
- [x] expose count-to-infinity behavior for classic mode and mitigation for poison reverse
- [x] add Markdown/Mermaid timeline export for a focused destination across routers
- [x] document the new failure/timeline workflow in the project README
- [x] add unit tests for reconvergence history and CLI timeline output
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-15 triggered updates slice
- [x] brief research note captured
- [x] short refresh and self-test captured
- [x] add a resumable slice checklist entry
- [x] implement explicit periodic vs triggered update scheduling modes
- [x] expose active routers in round history for schedule inspection
- [x] document update-strategy usage in the project README
- [x] add unit tests for triggered scheduling and CLI support
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-22 failure benchmark slice
- [x] brief research note captured
- [x] short refresh and self-test captured
- [x] add a resumable slice checklist entry
- [x] implement failure benchmark comparison across routing modes and update strategies
- [x] add JSON, CSV, and Markdown benchmark output paths plus checked-in sample artifacts
- [x] document benchmark usage in the project README
- [x] add unit tests for benchmark helpers, deduping, and CLI CSV output
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-22 failure suite slice
- [x] brief research note captured
- [x] short refresh and self-test captured
- [x] add a resumable slice checklist entry
- [x] add curated built-in failure scenarios beyond the tiny `A-B-C` loop
- [x] implement suite aggregation and scorecards across scenarios
- [x] add JSON, CSV, and Markdown suite output paths plus checked-in sample artifacts
- [x] document suite usage and scenario names in the project README
- [x] add unit tests for suite helpers, curated scenarios, and CLI CSV output
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## Future improvements
- [x] add Graphviz or Mermaid export for topology and route snapshots
- [x] simulate periodic timers vs triggered updates explicitly
- [x] add count-to-infinity demo scenarios with per-round timeline artifacts
- [x] compare convergence length across modes on larger benchmark scenarios
- [ ] render neighbor-to-neighbor advertisement messages explicitly, not only final per-round tables
- [x] extend the failure benchmark to run larger topology suites automatically
- [ ] add per-route timeout / garbage-collection timers closer to RIP behavior
