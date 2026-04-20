# Dependency graph walkthrough — Resource Graph

- Source manifest: `projects/dependency-graph-planner/resource_graph.json`
- Task count: `5`
- Parallel layers: `3`
- Estimated makespan: `6`
- Critical path: `prep -> gpu-train -> package`
- Worker-limited makespan (3 workers): `8`
- Worker-limited strategy: `critical-first`

## Linked artifacts

- [GitHub-friendly Mermaid preview](resource_graph_mermaid.md)
- [Mermaid source](resource_graph.mmd)
- [Graphviz DOT source](resource_graph.dot)
- [Report dashboard HTML](resource_graph_resource_report_dashboard.html)
- [Worker-limited schedule SVG](resource_graph_3_workers_schedule.svg)
- [Worker-limited schedule JSON](resource_graph_3_workers_schedule.json)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `prep, docs, gpu-eval, gpu-train, package`
- widest parallel layer: `layer 1` with `3` task(s): `docs`, `gpu-eval`, `gpu-train`
- non-critical slack budget available for schedule tradeoffs: `3` time units
- worker-limited dispatch uses critical-first, low-slack, longer-duration tie-breaking across `3 workers`
- worker cap increases makespan by `2` time unit(s) over the unlimited-layer bound of `6`
- utilization under the worker cap: `45.8%` with `13` idle worker-time unit(s)
- biggest queue delay: `gpu-eval` waited `4` time unit(s) after becoming ready on `gpu#1`
- renewable resource caps active for the constrained run: `gpu=1`
- compared worker caps against the unlimited baseline of `6`: `3 workers → 8`

## Parallel layer windows

- Layer 0 (`0` → `1`): `prep`
- Layer 1 (`1` → `5`): `docs`, `gpu-eval`, `gpu-train`
- Layer 2 (`5` → `6`): `package`

## Worker-capacity comparison

| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 workers | 8 | 2 | 6 | 45.8% | 13 | 1 | 4 |

## Worker-limited comparison

- Worker limit: `3`
- Strategy: `critical-first`
- Total work: `11`
- Theoretical lower bound: `6`
- Unlimited layered makespan: `6`
- Worker-limited makespan: `8`
- Dispatch order: `prep, gpu-train, docs, gpu-eval, package`

### Worker timelines

- Worker 1 (`0 → 8`): prep (0→1), gpu-train (1→5) [gpu#1], gpu-eval (5→7) [gpu#1], package (7→8)
- Worker 2 (`1 → 4`): docs (1→4)
- Worker 3: `idle for the full run`

### Resource-class utilization

| Resource class | Capacity | Tasks | Reserved units | Peak concurrent usage | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gpu | 1 | 2 | 6 | 1 | 75.0% | 2 | 1 | 4 |

### Worker-limited task table

| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| prep | 1 | — | — | 0 | 0 | 1 | 0 | yes |
| gpu-train | 1 | gpu | gpu#1 | 1 | 1 | 5 | 0 | yes |
| docs | 2 | — | — | 1 | 1 | 4 | 0 | no |
| gpu-eval | 1 | gpu | gpu#1 | 1 | 5 | 7 | 4 | no |
| package | 1 | — | — | 7 | 7 | 8 | 0 | yes |

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| prep | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | python scripts/prepare_dataset.py |
| docs | 1 | prep | 3 | — | 1 | 4 | 2 | 5 | 1 | no | mkdocs build |
| gpu-eval | 1 | prep | 2 | gpu | 1 | 3 | 3 | 5 | 2 | no | python eval.py --checkpoint best.pt |
| gpu-train | 1 | prep | 4 | gpu | 1 | 5 | 1 | 5 | 0 | yes | python train.py --epochs 5 |
| package | 2 | gpu-train, gpu-eval, docs | 1 | — | 5 | 6 | 5 | 6 | 0 | yes | python -m build |

## Deterministic execution order

1. `prep`
   - Dependencies: `ready at start`
   - Window: `0 → 1`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python scripts/prepare_dataset.py`
2. `docs`
   - Dependencies: `prep`
   - Window: `1 → 4`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `mkdocs build`
3. `gpu-eval`
   - Dependencies: `prep`
   - Window: `1 → 3`
   - Slack: `2`
   - Resources: `gpu`
   - Command: `python eval.py --checkpoint best.pt`
4. `gpu-train`
   - Dependencies: `prep`
   - Window: `1 → 5`
   - Slack: `0`
   - Resources: `gpu`
   - Command: `python train.py --epochs 5`
5. `package`
   - Dependencies: `gpu-train`, `gpu-eval`, `docs`
   - Window: `5 → 6`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python -m build`
