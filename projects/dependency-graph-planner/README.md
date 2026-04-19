# Dependency Graph Planner

A compact Python project that models a build or delivery workflow as a directed acyclic graph, validates dependencies, produces a deterministic execution plan, computes parallel layers, highlights the critical path, and exports recruiter-friendly diagrams plus walkthrough reports.

## Why this project is portfolio-worthy
- demonstrates core graph algorithms that show up in build systems, CI pipelines, schedulers, and package managers
- turns DAG theory into a runnable CLI with cycle detection, topological sorting, timing analysis, and visual exports
- gives you concrete interview material for dependency resolution, parallel scheduling, critical-path tradeoffs, and artifact generation
- stays lightweight and dependency-free so the implementation is easy to study and extend

## Features
- JSON manifest loader with structural validation
- deterministic topological order for reproducible plans
- cycle detection with a human-readable cycle trace
- parallel layer generation for "what can run together" views
- critical-path and slack calculation using task durations
- CLI output in text or JSON form for scripting
- Mermaid and Graphviz DOT diagram export with per-layer grouping and critical-path highlighting
- recruiter-friendly Markdown walkthrough reports that bundle layer windows, timing tables, deterministic order, and relative links to companion diagram artifacts

## Project structure
- `dependency_graph_planner.py` - parser, graph algorithms, timing analysis, CLI, diagram export helpers, and walkthrough-report generation
- `sample_graph.json` - example build-style workflow manifest
- `test_dependency_graph_planner.py` - unit and CLI tests
- `docs/artifacts/dependency-graph-planner/` - committed sample Mermaid, Markdown-wrapper, DOT, and walkthrough-report outputs from the example graph

## Manifest format
```json
{
  "tasks": [
    {"name": "lint", "duration": 1},
    {"name": "compile", "deps": ["lint"], "duration": 4},
    {"name": "unit", "deps": ["compile"], "duration": 2}
  ]
}
```

Fields:
- `name` - required unique task name
- `deps` - optional dependency list
- `duration` - optional positive integer duration, default `1`
- `command` - optional command string for documentation/demo purposes

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

Committed example artifacts:
- `docs/artifacts/dependency-graph-planner/sample_graph.mmd`
- `docs/artifacts/dependency-graph-planner/sample_graph_mermaid.md`
- `docs/artifacts/dependency-graph-planner/sample_graph.dot`
- `docs/artifacts/dependency-graph-planner/sample_graph_report.md`

## Testing
```bash
python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v
```

## Interview talking points
- why deterministic topological sorts are useful for reproducible tooling
- how layered execution exposes parallel work even when the overall graph is dependency-constrained
- why the critical path, not total task count, often dominates end-to-end completion time
- why Mermaid and DOT are useful complementary export targets for README-friendly diagrams versus richer offline rendering
- how a recruiter-friendly report can reuse deterministic plan/timing data without requiring terminal screenshots
- what kinds of product choices can change slack, bottlenecks, or scheduling fairness

## Future improvements
- add resource constraints so plans can respect limited workers, cores, or environments
- support weighted heuristics such as longest-processing-time-first within ready queues
- simulate execution traces and compare heuristic schedulers on the same DAG
- add constrained-schedule reports that compare unlimited-layer timing versus worker-limited execution
