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


## Benchmark artifact export slice (2026-04-19 15:56 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because benchmark artifact export is already the clearest unfinished follow-up in the README/checklist
- [x] skip extra language refresh because the slice stays inside existing Python CLI/report-generation patterns already used across this repo
- [x] update/add checklist docs so the slice is resumable
- [x] add CSV export for per-run Tarjan vs Kosaraju timing rows
- [x] add Markdown benchmark-report export with graph summary, averages, trial rows, and component roster
- [x] expose the new compare export workflow in the README
- [x] extend automated coverage for render helpers and CLI artifact writing
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Benchmark HTML dashboard slice (2026-04-20 19:30 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because the HTML benchmark dashboard is already the clearest unfinished follow-up in the README/checklist
- [x] do a short Python static-artifact/relative-link self-test while planning the slice
- [x] update/add checklist docs so the slice is resumable
- [x] add direct `--json-output` support so compare artifact bundles no longer depend on shell redirection
- [x] add a static `--html-output` benchmark dashboard with summary cards, per-trial timing bars, component cards, and sibling artifact links
- [x] expose the new compare export workflow in the README
- [x] extend automated coverage for HTML rendering, relative artifact links, and CLI artifact writing
- [x] generate a committed sample HTML artifact bundle under `docs/artifacts/tarjan-scc-lab/`
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Benchmark PNG capture slice (2026-04-20 20:02 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] do brief web research on headless Chrome screenshot flags for local HTML files
- [x] do a short Chrome headless / viewport-sizing self-test before coding
- [x] update/add checklist docs so the slice is resumable
- [x] add compare-command PNG capture helpers on top of the HTML dashboard export
- [x] expose the new PNG workflow in the README and checked-in artifact bundle
- [x] extend automated coverage for PNG command building, render flow, and CLI guardrails
- [x] generate a committed sample PNG artifact under `docs/artifacts/tarjan-scc-lab/`
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Showcase landing-page slice (2026-04-20 20:23 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because the showcase shape can reuse existing repo-local static artifact patterns and Tarjan already has the needed data exports
- [x] do a short Python/static-link self-test while planning the slice
- [x] update/add checklist docs so the slice is resumable
- [x] add a `showcase-demo` command that turns the Tarjan graph summary into a combined Markdown/HTML landing page
- [x] embed an explanation preview plus topology-group summary cards so the page reads well even before clicking out to raw artifacts
- [x] validate supplied artifact links and support relative links to explain/condensation/benchmark companion files
- [x] refresh the committed sample artifact bundle with explanation, condensation, and showcase outputs
- [x] update the README with the new showcase workflow
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up

## Next slice candidates
- [x] export the condensation DAG as Graphviz for portfolio screenshots
- [x] export the condensation DAG as Mermaid for markdown-native demos
- [x] compare Tarjan and Kosaraju implementations with the same fixtures and benchmark output
- [x] add in-degree/out-degree bottleneck summaries per SCC in the condensation graph
- [x] support topological ordering groups directly in JSON for downstream tooling
- [x] export benchmark comparisons as CSV/markdown artifacts for portfolio screenshots
- [x] add a small HTML benchmark card/gallery that reuses the compare JSON/CSV artifact bundle

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
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Topology-groups JSON slice (2026-04-16 10:41 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current Tarjan SCC lab for the weakest unfinished portfolio gap
- [x] skip web research because grouped topological levels are already the clearest next downstream-tooling extension in the README/checklist
- [x] do a short Python SCC/topology-group self-test while planning the slice
- [x] update/add checklist docs so the slice is resumable
- [x] add `topology_groups` to SCC summary and condensation JSON output so consumers get layered component groups directly
- [x] expose the new grouped JSON shape in the README with a concrete example
- [x] extend automated coverage for grouped JSON payloads and CLI behavior
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
