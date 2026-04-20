# Dependency Graph Planner Research — 2026-04-20 — synthetic generator slice

## Goal
Add generated workload families so the dependency-graph planner showcases more realistic CS scheduling stories without manually maintaining a large pile of one-off JSON DAGs.

## Brief references checked
- GitHub Actions docs on matrix job variations: highlighted fan-out/fan-in workflow shapes where one logical job expands into many parallel runs across a strategy matrix.
- Google Cloud Deploy canary docs: reinforced that progressive delivery is commonly modeled as staged percentage rollouts with validation gates between phases.
- dbt model docs: reinforced that warehouse/data workflows naturally form layered dependency graphs where many transformations feed later feature/model/publishing steps.

## Notes carried into implementation
- CI generator should visibly fan out after build/install and then fan back in through packaging/deploy/smoke gates.
- Release generator should serialize scarce signing capacity and model canary rollout as repeated deploy/verify pairs before full rollout.
- Data-pipeline generator should highlight warehouse bottlenecks, partition fan-out, and a late GPU-bound ML stage.
- The output should stay synthetic and deterministic rather than pretending to be vendor-accurate YAML, because the portfolio goal is scheduling structure, not a full workflow-engine clone.
