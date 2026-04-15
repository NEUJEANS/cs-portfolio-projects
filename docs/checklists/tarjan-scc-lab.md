# tarjan-scc-lab checklist

- [x] choose a portfolio-worthy SCC/graph-analysis concept with strong algorithms interview value
- [x] implement Tarjan SCC extraction, graph loading, condensation DAG export, and readable CLI flows
- [x] add README usage, design notes, and future ideas
- [x] add automated tests for parsing, SCC grouping, condensation output, and CLI behavior
- [x] log at least 3 review passes
- [x] keep extending the lab with visualization or analysis slices that are easy to demo in interviews

## Topological condensation levels slice (2026-04-15 13:21 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because condensation-level annotation is a direct graph-DAG extension of the current implementation
- [x] do a short Python DAG/topological-propagation self-check while planning the slice
- [x] update/add checklist docs so the slice is resumable
- [x] add topological level annotations to SCC summaries and condensation DAG output
- [x] expose the levels in `explain` output and README examples
- [x] extend automated coverage for level propagation and CLI behavior
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Next slice candidates
- [ ] export the condensation DAG as Graphviz or Mermaid for portfolio screenshots
- [ ] compare Tarjan and Kosaraju implementations with the same fixtures and benchmark output
- [ ] add in-degree/out-degree bottleneck summaries per SCC in the condensation graph
- [ ] support topological ordering groups directly in JSON for downstream tooling
