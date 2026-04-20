# Dependency Graph Planner

A compact Python project that models a build or delivery workflow as a directed acyclic graph, validates dependencies, produces a deterministic execution plan, computes parallel layers, highlights the critical path, and exports recruiter-friendly diagrams plus walkthrough reports.

## Why this project is portfolio-worthy
- demonstrates core graph algorithms that show up in build systems, CI pipelines, schedulers, and package managers
- turns DAG theory into a runnable CLI with cycle detection, topological sorting, timing analysis, and constrained scheduling
- gives you concrete interview material for dependency resolution, parallel scheduling, critical-path tradeoffs, and scarce-runner bottlenecks
- stays lightweight and dependency-free so the implementation is easy to study and extend

## Features
- JSON manifest loader with structural validation
- deterministic topological order for reproducible plans
- cycle detection with a human-readable cycle trace
- parallel layer generation for “what can run together” views
- critical-path and slack calculation using task durations
- deterministic worker-limited list scheduling with queue-delay tracking for realistic single-worker or small-runner scenarios
- renewable resource constraints so schedules can model scarce runners such as GPUs, signing hosts, and browser labs
- per-task multi-resource demand vectors via `resources` plus backwards-compatible single-resource `resource_class`
- selectable ready-queue strategies (`critical-first`, `fifo`, and `longest-processing-time`) for comparing scheduler tradeoffs on the same DAG
- CLI output in text or JSON form for scripting
- Mermaid and Graphviz DOT diagram export with per-layer grouping and critical-path highlighting
- recruiter-friendly Markdown walkthrough reports that bundle layer windows, timing tables, deterministic order, worker/resource comparisons, and linked diagram/schedule artifacts
- compact static HTML dashboards that turn each report bundle into a README-friendly landing page with relative links and embedded schedule previews
- GitHub-friendly SVG schedule timelines for constrained runs so reviewers can inspect worker/resource bottlenecks without opening raw JSON
- synthetic manifest generators for CI, release, and data-pipeline bottleneck stories so the project can showcase multiple workload families without hand-authoring every DAG
- batch benchmark-suite mode that replays many manifests, ranks scheduling strategies, and emits a scoreboard-style Markdown summary across both hand-authored and generated manifests

## Project structure
- `dependency_graph_planner.py` - parser, graph algorithms, timing analysis, scheduler, CLI, diagram export helpers, walkthrough-report generation, HTML dashboard rendering, and schedule SVG export
- `sample_graph.json` - example build-style workflow manifest
- `resource_graph.json` - example manifest showing how a single scarce renewable resource serializes otherwise parallel-ready work
- `strategy_graph.json` - example manifest that makes scheduling-strategy tradeoffs visible under a fixed worker cap
- `multi_resource_graph.json` - example manifest showing tasks that need multiple renewable resources at once
- `portfolio_benchmark_suite.json` - example benchmark suite that replays the committed showcase manifests in one batch
- `generated_ci_pipeline.json` - generated CI-style showcase manifest with matrix-like unit-test fan-out, artifact packaging, preview deploy, and smoke coverage
- `generated_release_pipeline.json` - generated release-engineering showcase manifest with platform builds, serialized signing, and progressive canary rollout
- `generated_data_pipeline.json` - generated warehouse/ML showcase manifest with partition fan-out, bottlenecked transforms, feature building, and GPU training
- `test_dependency_graph_planner.py` - unit and CLI tests
- `CHECKLIST.md` - resumable slice tracker for future portfolio work on this project
- `docs/artifacts/dependency-graph-planner/` - committed Mermaid, DOT, report, and schedule outputs from the sample manifests

## Manifest format
```json
{
  "resource_capacities": {
    "gpu": 1,
    "browser-lab": 2
  },
  "tasks": [
    {"name": "lint", "duration": 1},
    {"name": "train", "deps": ["lint"], "duration": 4, "resource_class": "gpu"},
    {
      "name": "cross-platform-cert",
      "deps": ["lint"],
      "duration": 2,
      "resources": {"gpu": 1, "browser-lab": 1}
    }
  ]
}
```

Task fields:
- `name` - required unique task name
- `deps` - optional dependency list
- `duration` - optional positive integer duration, default `1`
- `command` - optional command string for documentation/demo purposes
- `resource_class` - optional single renewable resource label for legacy/simple cases
- `resources` - optional object mapping renewable resource labels to positive integer per-task demand counts

Top-level fields:
- `resource_capacities` - optional object mapping renewable resource names to positive integer capacities used by `schedule` / `report`

Notes:
- `resource_class` is treated as shorthand for `resources: {"that-class": 1}`
- when both are present, `resource_class` must not duplicate a key already listed in `resources`
- resource-aware scheduling/reporting requires capacities for every declared renewable resource

## Benchmark suite format
```json
{
  "title": "Dependency graph strategy benchmark suite",
  "scenarios": [
    {"label": "sample-2-workers", "graph": "sample_graph.json", "worker_limit": 2},
    {
      "label": "multi-resource-browser-bump",
      "graph": "multi_resource_graph.json",
      "worker_limit": 3,
      "strategies": ["critical-first", "fifo"],
      "resource_capacities": {"browser-lab": 3, "gpu": 1, "signing": 1}
    }
  ]
}
```

Suite fields:
- `title` - optional report title override for the `benchmark` command
- `scenarios` - required non-empty list of benchmark cases

Scenario fields:
- `label` - required unique scenario name used in the Markdown report
- `graph` - required relative or absolute path to a dependency-graph manifest
- `worker_limit` - required positive worker cap for every strategy replay in that scenario
- `strategies` - optional subset of ready-queue strategies; defaults to all supported strategies
- `resource_capacities` - optional inline renewable-resource capacities that override the manifest for just that scenario

## Usage
Run from the repository root.

### Validate a manifest
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py validate \
  projects/dependency-graph-planner/sample_graph.json
```

### Show the full execution plan
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py plan \
  projects/dependency-graph-planner/sample_graph.json
```

### Extract only the critical path as JSON
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py critical-path \
  projects/dependency-graph-planner/sample_graph.json \
  --json
```

### Inspect parallel layers
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py layers \
  projects/dependency-graph-planner/sample_graph.json
```

### Simulate a worker-limited schedule
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule \
  projects/dependency-graph-planner/sample_graph.json \
  --worker-limit 1
```

### Simulate a schedule with scarce renewable resources
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule \
  projects/dependency-graph-planner/resource_graph.json \
  --worker-limit 3
```

### Inspect a task that needs multiple renewable resources at once
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule \
  projects/dependency-graph-planner/multi_resource_graph.json \
  --worker-limit 3 \
  --json
```

### Override a manifest resource capacity from the CLI
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule \
  projects/dependency-graph-planner/multi_resource_graph.json \
  --worker-limit 3 \
  --resource-capacity browser-lab=3
```

### Compare different ready-queue strategies on the same worker cap
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule \
  projects/dependency-graph-planner/strategy_graph.json \
  --worker-limit 2 \
  --strategy fifo
```

### Export a Mermaid dependency diagram
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py diagram \
  projects/dependency-graph-planner/sample_graph.json \
  --format mermaid \
  > /tmp/dependency-graph.mmd
```

### Export a Graphviz DOT dependency diagram
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py diagram \
  projects/dependency-graph-planner/sample_graph.json \
  --format dot \
  > /tmp/dependency-graph.dot
```

### Export a recruiter-friendly walkthrough report with linked diagrams
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/sample_graph.json \
  --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_report.md \
  --report-html-out docs/artifacts/dependency-graph-planner/sample_graph_report_dashboard.html \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked Markdown walkthrough plus a compact HTML landing page for the same artifact bundle.

### Compare unlimited execution against a constrained single-worker run
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/sample_graph.json \
  --worker-limit 1 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md \
  --report-html-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report_dashboard.html \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked report plus `sample_graph_single_worker_schedule.json` and `sample_graph_single_worker_schedule.svg` in the same artifact directory.

### Compare 1-worker, 2-worker, and 3-worker scenarios in one report
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/sample_graph.json \
  --worker-limit 1 \
  --compare-worker-limit 2 \
  --compare-worker-limit 3 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md \
  --report-html-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report_dashboard.html \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked comparison report plus JSON and SVG schedule snapshots for `1`, `2`, and `3` workers.

### Report a worker-limited run with renewable resource summaries
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/resource_graph.json \
  --worker-limit 3 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md \
  --report-html-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report_dashboard.html \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked report plus `resource_graph_3_workers_schedule.json` / `.svg` with per-task resource allocations and resource-utilization summaries.

### Report a multi-resource constrained run
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/multi_resource_graph.json \
  --worker-limit 3 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/multi_resource_graph_report.md \
  --report-html-out docs/artifacts/dependency-graph-planner/multi_resource_graph_report_dashboard.html \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked report plus `multi_resource_graph_3_workers_schedule.json` / `.svg` with per-task demand vectors, concrete slot allocations, and resource summary tables.

### Compare scheduling strategies at a fixed worker cap
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/strategy_graph.json \
  --worker-limit 2 \
  --compare-strategy fifo \
  --compare-strategy longest-processing-time \
  --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md \
  --report-html-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report_dashboard.html \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked strategy-comparison report plus JSON and SVG schedule snapshots for each compared strategy.

### Benchmark a suite of manifests
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py benchmark \
  projects/dependency-graph-planner/portfolio_benchmark_suite.json \
  --benchmark-markdown-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.md
```
This emits a scoreboard-style Markdown report that compares scheduling strategies across the committed sample, strategy, resource, multi-resource, and generated showcase manifests in one batch.

### Generate a synthetic CI / release / data-pipeline manifest
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py generate ci \
  --generator-width 4 \
  --generated-manifest-out projects/dependency-graph-planner/generated_ci_pipeline.json
```
Swap `ci` for `release` or `data-pipeline` to generate the other workload families. `--generator-width` scales unit-test shards, canary phases, or transform partitions depending on the selected generator.

### Export a generated manifest as a full recruiter-friendly artifact bundle
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/generated_release_pipeline.json \
  --worker-limit 3 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/generated_release_pipeline_report.md \
  --report-html-out docs/artifacts/dependency-graph-planner/generated_release_pipeline_report_dashboard.html \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the generated release manifest's walkthrough report plus diagram, JSON, and SVG schedule artifacts.

Committed example artifacts:
- `docs/artifacts/dependency-graph-planner/sample_graph.mmd`
- `docs/artifacts/dependency-graph-planner/sample_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/sample_graph.dot`
- `docs/artifacts/dependency-graph-planner/sample_graph_report.md`
- `docs/artifacts/dependency-graph-planner/sample_graph_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md`
- `docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md`
- `docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/sample_graph_single_worker_schedule.json`
- `docs/artifacts/dependency-graph-planner/sample_graph_single_worker_schedule.svg`
- `docs/artifacts/dependency-graph-planner/sample_graph_2_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/sample_graph_2_workers_schedule.svg`
- `docs/artifacts/dependency-graph-planner/sample_graph_3_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/sample_graph_3_workers_schedule.svg`
- `docs/artifacts/dependency-graph-planner/resource_graph.mmd`
- `docs/artifacts/dependency-graph-planner/resource_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/resource_graph.dot`
- `docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md`
- `docs/artifacts/dependency-graph-planner/resource_graph_resource_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/resource_graph_3_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/resource_graph_3_workers_schedule.svg`
- `docs/artifacts/dependency-graph-planner/strategy_graph.mmd`
- `docs/artifacts/dependency-graph-planner/strategy_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/strategy_graph.dot`
- `docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md`
- `docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_critical_first_schedule.json`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_critical_first_schedule.svg`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_fifo_schedule.json`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_fifo_schedule.svg`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_longest_processing_time_schedule.json`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_longest_processing_time_schedule.svg`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph.mmd`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph.dot`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_report.md`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_3_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_3_workers_schedule.svg`
- `docs/artifacts/dependency-graph-planner/generated_ci_pipeline.mmd`
- `docs/artifacts/dependency-graph-planner/generated_ci_pipeline_mermaid.md`
- `docs/artifacts/dependency-graph-planner/generated_ci_pipeline.dot`
- `docs/artifacts/dependency-graph-planner/generated_ci_pipeline_report.md`
- `docs/artifacts/dependency-graph-planner/generated_ci_pipeline_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/generated_ci_pipeline_4_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/generated_ci_pipeline_4_workers_schedule.svg`
- `docs/artifacts/dependency-graph-planner/generated_release_pipeline.mmd`
- `docs/artifacts/dependency-graph-planner/generated_release_pipeline_mermaid.md`
- `docs/artifacts/dependency-graph-planner/generated_release_pipeline.dot`
- `docs/artifacts/dependency-graph-planner/generated_release_pipeline_report.md`
- `docs/artifacts/dependency-graph-planner/generated_release_pipeline_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/generated_release_pipeline_3_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/generated_release_pipeline_3_workers_schedule.svg`
- `docs/artifacts/dependency-graph-planner/generated_data_pipeline.mmd`
- `docs/artifacts/dependency-graph-planner/generated_data_pipeline_mermaid.md`
- `docs/artifacts/dependency-graph-planner/generated_data_pipeline.dot`
- `docs/artifacts/dependency-graph-planner/generated_data_pipeline_report.md`
- `docs/artifacts/dependency-graph-planner/generated_data_pipeline_report_dashboard.html`
- `docs/artifacts/dependency-graph-planner/generated_data_pipeline_4_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/generated_data_pipeline_4_workers_schedule.svg`
- `docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.md`

## Testing
```bash
python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v
```

## Interview talking points
- why deterministic topological sorts are useful for reproducible tooling
- how layered execution exposes parallel work even when the overall graph is dependency-constrained
- why the critical path, not total task count, often dominates end-to-end completion time
- why worker caps expose queue delay even on a valid DAG and why that matters for CI runners or deployment gates
- how renewable resource constraints extend a plain worker-cap demo toward real runner pools such as GPUs, signing hosts, or browser labs
- why multi-resource demand vectors are closer to real release engineering than a single-label toy scheduler
- how a benchmark suite makes it obvious when one heuristic wins, ties, or loses across different workload shapes
- why synthetic CI, release, and data-pipeline generators make the scheduler story broader without burying the repo in hand-authored DAGs
- what kinds of product choices can change slack, bottlenecks, or scheduling fairness

## Future improvements
- simulate execution traces or stochastic duration changes to compare heuristic robustness under uncertainty
- add optional randomized stress tests that compare heuristic schedules against the critical-path lower bound
- export CSV/JSON leaderboard snapshots for downstream plotting or notebook analysis
- use manifest metadata automatically for default report/dashboard titles and richer artifact subtitles
