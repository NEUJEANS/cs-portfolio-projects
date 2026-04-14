# Dependency Graph Planner Research - 2026-04-14

## Goal
Add a new project that expands the portfolio into graph scheduling and build-planning concepts after the existing batch list was already broadly covered.

## Brief references checked
- topological sorting references for deterministic dependency ordering
- DAG scheduling/build-planner explanations tying dependency graphs to layered parallel execution
- critical-path method references for longest-path timing analysis and slack

## Notes carried into implementation
- use a DAG manifest that is easy to inspect and version-control, so JSON is enough for the first slice
- make the topological order deterministic to keep tests and interview demos stable
- include explicit cycle reporting because dependency tooling is most useful when it explains why a graph is invalid
- expose both layered execution and critical-path output so the project covers scheduling and analysis, not just ordering
- keep the implementation dependency-free; this is a portfolio lab, not a wrapper around a graph library
