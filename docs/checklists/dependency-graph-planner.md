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

## 2026-04-20 benchmark suite slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the locally modified planner file
- [x] capture a brief slice note explaining why extra external web research was not needed for this incremental benchmark/reporting follow-up
- [x] refresh expected benchmark outcomes for the sample, strategy, resource, and multi-resource showcase manifests before editing
- [x] update the project checklist, README, and artifact references for the new benchmark workflow
- [x] implement a `benchmark` command that loads a suite file, replays multiple manifests, ranks strategies, and exports Markdown/JSON summaries
- [x] commit a dedicated `portfolio_benchmark_suite.json` showcase file plus a recruiter-friendly benchmark report artifact
- [x] expand regression coverage for relative suite graph paths, inline resource-capacity overrides, strategy subsets, and benchmark-flag validation
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 report dashboard + SVG artifact slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the locally modified planner file
- [x] capture a brief note explaining why extra external web research was not needed for this incremental report/dashboard follow-up
- [x] refresh deterministic artifact-linking and schedule-SVG naming expectations before editing
- [x] update the project checklist, README, and artifact references for report dashboards and schedule SVG outputs
- [x] implement `--report-html-out` plus compact static dashboard rendering for committed walkthrough bundles
- [x] export GitHub-friendly SVG schedule timelines alongside the existing schedule JSON artifacts
- [x] expand regression coverage for dashboard rendering, SVG generation, artifact writing, and relative-link handling
- [x] regenerate committed report/dashboard/schedule artifacts for the sample, comparison, resource, strategy, and multi-resource showcase manifests
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 synthetic generator slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the dirty local dependency-graph-planner slice
- [x] do brief workflow-shape research on matrix CI fan-out, progressive canaries, and dbt-style warehouse/model pipelines
- [x] refresh generator-shape expectations and capture a short self-test note
- [x] update the project checklist, README, benchmark suite, and artifact references for generated showcase manifests
- [x] implement `generate` support for CI, release, and data-pipeline synthetic manifests with width scaling
- [x] add regression coverage for generated manifests, invalid generator flag usage, and repo-relative source labels in committed reports
- [x] commit generated manifest JSON files plus report/dashboard/diagram/schedule artifacts for the new showcase families
- [x] rerun the benchmark suite so the scoreboard now includes both hand-authored and generated workload families
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 benchmark export slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the dirty local dependency-graph-planner slice
- [x] capture a brief slice note explaining why extra external web research was not needed for this incremental benchmark-export follow-up
- [x] refresh Python CSV/JSON export expectations and capture a short self-test note
- [x] update the project checklist, README, and artifact references for benchmark JSON/CSV exports
- [x] implement `--benchmark-json-out`, `--benchmark-aggregate-csv-out`, and `--benchmark-strategy-csv-out`
- [x] add regression coverage for repo-relative graph labels, artifact writing, and benchmark-flag misuse on non-benchmark commands
- [x] commit the benchmark JSON + CSV artifact set beside the existing Markdown report
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 benchmark dashboard slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the dirty local dependency-graph-planner slice
- [x] continue the unfinished local benchmark-dashboard slice instead of starting a competing change
- [x] capture a brief slice note explaining why extra external web research was not needed for this incremental artifact-rendering follow-up
- [x] refresh static HTML dashboard and relative-link expectations with a short self-test note
- [x] update the project checklist, README, and artifact references for benchmark HTML dashboards
- [x] implement `--benchmark-html-out` plus a compact static dashboard renderer over the existing benchmark result payload
- [x] add regression coverage for dashboard rendering, artifact linking, artifact writing, and benchmark-flag misuse on non-benchmark commands
- [x] commit the benchmark dashboard artifact beside the existing Markdown/JSON/CSV suite exports
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 stress benchmark slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the dirty local dependency-graph-planner slice
- [x] continue the unfinished local stress-benchmark slice instead of starting a competing change
- [x] capture a brief slice note explaining why extra external web research was not needed for this incremental scheduling-benchmark follow-up
- [x] refresh deterministic seeded-generator and critical-path-lower-bound expectations with a short self-test note
- [x] update the project checklist, README, benchmark suite, and artifact references for seeded stress scenarios and lower-bound metrics
- [x] implement the `stress` synthetic generator plus benchmark gap/ratio reporting versus the critical-path lower bound across Markdown, HTML, JSON, and CSV outputs
- [x] add regression coverage for seeded stress generation and the benchmark dashboard summary-card logic
- [x] commit seeded stress manifests plus regenerated benchmark-suite artifacts under `docs/artifacts/`
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-20 stochastic benchmark slice
- [x] confirm the repo was still synced with `origin/main` before continuing from the dirty local dependency-graph-planner slice
- [x] continue the unfinished local stochastic-benchmark slice instead of starting a competing change
- [x] capture a brief slice note explaining why extra external web research was not needed for this incremental uncertainty-benchmark follow-up
- [x] refresh triangular-duration replay expectations and capture a short self-test note
- [x] update the project checklist, slice checklist, README, benchmark suite, and artifact references for stochastic-duration scenarios
- [x] implement seeded stochastic benchmark replays and aggregate robustness reporting across Markdown, HTML, JSON, and CSV outputs
- [x] add regression coverage for stochastic benchmark payloads and invalid stochastic-duration configs
- [x] regenerate the committed benchmark-suite artifact bundle so the repo browser shows the new robustness story immediately
- [x] run tests and command-line smoke checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up
