# Dependency Graph Planner

A compact Python project that models a build or delivery workflow as a directed acyclic graph, validates dependencies, produces a deterministic execution plan, computes parallel layers, and highlights the critical path.

## Why this project is portfolio-worthy
- demonstrates core graph algorithms that show up in build systems, CI pipelines, schedulers, and package managers
- turns DAG theory into a runnable CLI with cycle detection, topological sorting, and timing analysis
- gives you concrete interview material for dependency resolution, parallel scheduling, and critical-path tradeoffs
- stays lightweight and dependency-free so the implementation is easy to study and extend

## Features
- JSON manifest loader with structural validation
- deterministic topological order for reproducible plans
- cycle detection with a human-readable cycle trace
- parallel layer generation for "what can run together" views
- critical-path and slack calculation using task durations
- CLI output in text or JSON form for scripting

## Project structure
- `dependency_graph_planner.py` - parser, graph algorithms, timing analysis, and CLI
- `sample_graph.json` - example build-style workflow manifest
- `test_dependency_graph_planner.py` - unit and CLI tests

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

## Testing
```bash
python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v
```

## Interview talking points
- why deterministic topological sorts are useful for reproducible tooling
- how layered execution exposes parallel work even when the overall graph is dependency-constrained
- why the critical path, not total task count, often dominates end-to-end completion time
- what kinds of product choices can change slack, bottlenecks, or scheduling fairness

## Future improvements
- export Graphviz DOT or Mermaid diagrams for visual dependency maps
- add resource constraints so plans can respect limited workers, cores, or environments
- support weighted heuristics such as longest-processing-time-first within ready queues
- simulate execution traces and compare heuristic schedulers on the same DAG
