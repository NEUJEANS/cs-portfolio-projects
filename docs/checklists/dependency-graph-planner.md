# Dependency Graph Planner Checklist

## 2026-04-14 initial build slice
- [x] brief research note captured
- [x] short refresh and self-test captured
- [x] create project scaffold and README
- [x] implement manifest validation, deterministic planning, layered execution, and critical-path analysis
- [x] add unit tests and CLI tests
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 diagram export slice
- [x] do brief research on Mermaid flowchart and Graphviz DOT export constraints
- [x] refresh Mermaid/DOT export patterns and capture a short self-test note
- [x] update project docs and checklist for the diagram-export slice
- [x] implement Mermaid and Graphviz DOT dependency-diagram export with layer grouping and critical-path highlighting
- [x] add regression coverage for direct render helpers and CLI output
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 walkthrough report slice
- [x] do brief research on GitHub-friendly Markdown diagram/report linking
- [x] refresh Markdown report-export patterns and capture a short self-test note
- [x] update project docs and checklist for the walkthrough-report slice
- [x] implement a `report` workflow that emits recruiter-friendly Markdown walkthroughs plus linked Mermaid/DOT companion artifacts
- [x] add regression coverage for report rendering, artifact writing, and report-flag validation
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 worker-limited report slice
- [x] reuse the 2026-04-19 worker-limited scheduling research note for this resumable follow-up
- [x] reuse the 2026-04-19 worker-limited refresh/self-test note before editing
- [x] update project docs and checklist for the worker-limited report slice
- [x] implement worker-limited report support with linked schedule JSON artifact export
- [x] add regression coverage for report wording, schedule artifact writing, and relative links
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 multi-capacity comparison slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the locally modified planner file
- [x] reuse the 2026-04-19 worker-limited scheduling and report-export notes; no extra web research was needed for this incremental slice
- [x] refresh expected sample-graph makespans for 1-worker, 2-worker, and 3-worker runs before editing
- [x] update the project checklist, slice checklist, README, and artifact references for multi-capacity comparisons
- [x] implement repeatable `--compare-worker-limit` support for report rendering and multi-schedule artifact export
- [x] add regression coverage for comparison summaries/tables, multi-artifact links, deduped comparison limits, and compare-flag validation
- [x] regenerate committed comparison report artifacts and schedule JSON snapshots
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 strategy comparison slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the locally modified planner file
- [x] capture a brief slice note explaining why extra web research was not needed for this incremental scheduler-heuristic comparison
- [x] refresh expected strategy-graph makespans for `critical-first`, `fifo`, and `longest-processing-time` at `2 workers`
- [x] update the project checklist, README, and artifact references for strategy comparisons
- [x] implement selectable `--strategy` scheduling plus repeatable `--compare-strategy` report support
- [x] add regression coverage for strategy makespans, report tables, strategy artifact links, and CLI misuse handling
- [x] commit a dedicated `strategy_graph.json` showcase manifest plus regenerated report/diagram/schedule artifacts
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 renewable resource-class slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the locally modified planner file
- [x] do brief terminology research on RCPSP-style renewable resource capacities for DAG schedules
- [x] refresh expected resource-graph makespans for `gpu=1` vs `gpu=2` before editing
- [x] update the project checklist, README, and artifact references for resource-class constrained schedules
- [x] implement manifest-backed renewable resource capacities plus repeatable `--resource-capacity class=count` overrides for `schedule` / `report`
- [x] add recruiter-friendly report coverage for resource labels, slot assignments, and resource-utilization summaries
- [x] add regression coverage for resource-constrained schedules, override behavior, report output, and CLI misuse handling
- [x] commit a dedicated `resource_graph.json` showcase manifest plus Mermaid/DOT/report/schedule artifacts
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
