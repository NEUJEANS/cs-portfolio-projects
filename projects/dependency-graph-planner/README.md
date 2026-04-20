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
- batch benchmark-suite mode that replays many manifests, ranks scheduling strategies, and emits a scoreboard-style Markdown summary

## Project structure
- `dependency_graph_planner.py` - parser, graph algorithms, timing analysis, scheduler, CLI, diagram export helpers, and walkthrough-report generation
- `sample_graph.json` - example build-style workflow manifest
- `resource_graph.json` - example manifest showing how a single scarce renewable resource serializes otherwise parallel-ready work
- `strategy_graph.json` - example manifest that makes scheduling-strategy tradeoffs visible under a fixed worker cap
- `multi_resource_graph.json` - example manifest showing tasks that need multiple renewable resources at once
- `portfolio_benchmark_suite.json` - example benchmark suite that replays the committed showcase manifests in one batch
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
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```

### Compare unlimited execution against a constrained single-worker run
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/sample_graph.json \
  --worker-limit 1 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked report plus `sample_graph_single_worker_schedule.json` in the same artifact directory.

### Compare 1-worker, 2-worker, and 3-worker scenarios in one report
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/sample_graph.json \
  --worker-limit 1 \
  --compare-worker-limit 2 \
  --compare-worker-limit 3 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked comparison report plus `sample_graph_single_worker_schedule.json`, `sample_graph_2_workers_schedule.json`, and `sample_graph_3_workers_schedule.json`.

### Report a worker-limited run with renewable resource summaries
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/resource_graph.json \
  --worker-limit 3 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked report plus `resource_graph_3_workers_schedule.json` with per-task resource allocations and resource-utilization summaries.

### Report a multi-resource constrained run
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/multi_resource_graph.json \
  --worker-limit 3 \
  --report-markdown-out docs/artifacts/dependency-graph-planner/multi_resource_graph_report.md \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked report plus `multi_resource_graph_3_workers_schedule.json` with per-task demand vectors, concrete slot allocations, and resource summary tables.

### Compare scheduling strategies at a fixed worker cap
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py report \
  projects/dependency-graph-planner/strategy_graph.json \
  --worker-limit 2 \
  --compare-strategy fifo \
  --compare-strategy longest-processing-time \
  --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md \
  --diagram-output-dir docs/artifacts/dependency-graph-planner
```
This emits the linked strategy-comparison report plus `strategy_graph_2_workers_critical_first_schedule.json`, `strategy_graph_2_workers_fifo_schedule.json`, and `strategy_graph_2_workers_longest_processing_time_schedule.json`.

### Benchmark a suite of manifests
```bash
python3 projects/dependency-graph-planner/dependency_graph_planner.py benchmark \
  projects/dependency-graph-planner/portfolio_benchmark_suite.json \
  --benchmark-markdown-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.md
```
This emits a scoreboard-style Markdown report that compares scheduling strategies across the committed sample, strategy, resource, and multi-resource manifests in one batch.

Committed example artifacts:
- `docs/artifacts/dependency-graph-planner/sample_graph.mmd`
- `docs/artifacts/dependency-graph-planner/sample_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/sample_graph.dot`
- `docs/artifacts/dependency-graph-planner/sample_graph_report.md`
- `docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md`
- `docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md`
- `docs/artifacts/dependency-graph-planner/sample_graph_single_worker_schedule.json`
- `docs/artifacts/dependency-graph-planner/sample_graph_2_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/sample_graph_3_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/resource_graph.mmd`
- `docs/artifacts/dependency-graph-planner/resource_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/resource_graph.dot`
- `docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md`
- `docs/artifacts/dependency-graph-planner/resource_graph_3_workers_schedule.json`
- `docs/artifacts/dependency-graph-planner/strategy_graph.mmd`
- `docs/artifacts/dependency-graph-planner/strategy_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/strategy_graph.dot`
- `docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_critical_first_schedule.json`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_fifo_schedule.json`
- `docs/artifacts/dependency-graph-planner/strategy_graph_2_workers_longest_processing_time_schedule.json`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph.mmd`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph.dot`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_report.md`
- `docs/artifacts/dependency-graph-planner/multi_resource_graph_3_workers_schedule.json`
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
- what kinds of product choices can change slack, bottlenecks, or scheduling fairness

## Future improvements
- export compact HTML/SVG dashboards for README-first browsing without opening raw schedule JSON
- simulate execution traces or stochastic duration changes to compare heuristic robustness under uncertainty
- add synthetic manifest generators for CI, release, and data-pipeline scheduling patterns
- export CSV/JSON leaderboard snapshots for downstream plotting or notebook analysis
