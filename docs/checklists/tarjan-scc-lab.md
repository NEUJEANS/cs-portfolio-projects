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


## Graphviz condensation export slice (2026-04-15 13:59 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because Graphviz DOT export is a direct presentational extension of the existing condensation DAG
- [x] do a short Python string/CLI self-check while planning the slice
- [x] update/add checklist docs so the slice is resumable
- [x] add a Graphviz DOT export for the condensation DAG with component level and size labels
- [x] expose the new export in `README.md` and the CLI
- [x] extend automated coverage for DOT generation and CLI behavior
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up


## Mermaid condensation export slice (2026-04-15 14:09 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because Mermaid export is a direct markdown-friendly follow-up to the existing DOT export
- [x] do a short Mermaid flowchart label/self-test before coding
- [x] update/add checklist docs so the slice is resumable
- [x] add a Mermaid flowchart export for the condensation DAG with topology-level groupings and component labels
- [x] expose the new export in `README.md` and the CLI
- [x] extend automated coverage for Mermaid rendering, CLI behavior, and label escaping
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Tarjan vs Kosaraju comparison slice (2026-04-15 16:32 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because Kosaraju comparison is already listed as the next algorithmic extension in the project README/checklist
- [x] do a short SCC/transposed-graph refresh and self-test while planning the slice
- [x] update/add checklist docs so the slice is resumable
- [x] add a Kosaraju SCC implementation that uses the same graph fixtures and deterministic component ordering
- [x] add a comparison/benchmark CLI view that reports agreement and timing for Tarjan vs Kosaraju
- [x] expose the new comparison flow in the README
- [x] extend automated coverage for the new algorithm, comparison output, and CLI behavior
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Next slice candidates
- [x] export the condensation DAG as Graphviz for portfolio screenshots
- [x] export the condensation DAG as Mermaid for markdown-native demos
- [x] compare Tarjan and Kosaraju implementations with the same fixtures and benchmark output
- [x] add in-degree/out-degree bottleneck summaries per SCC in the condensation graph
- [ ] support topological ordering groups directly in JSON for downstream tooling

## Bottleneck summary slice (2026-04-16 02:11 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because SCC bottleneck summaries are already the clearest next extension in the README/checklist
- [x] do a short SCC condensation self-check while planning the slice
- [x] update/add checklist docs so the slice is resumable
- [x] add incoming/outgoing component counts and bottleneck roles to SCC summary + condensation JSON
- [x] expose the new metadata in the text explain flow and README examples
- [x] extend automated coverage for source/bridge/sink/isolated labeling
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [ ] run secret scan before push
- [ ] commit, push, and add wrap-up
