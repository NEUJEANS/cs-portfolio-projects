# Sample package release pipeline

Small packaging workflow that highlights deterministic dependency planning, a publish gate, and the extra delay introduced by a single constrained worker.

- Source manifest: `projects/dependency-graph-planner/sample_graph.json`
- Task count: `5`
- Parallel layers: `4`
- Estimated makespan: `8`
- Critical path: `lint -> compile -> unit -> publish`
- Worker-limited makespan (1 worker): `9`
- Worker-limited strategy: `critical-first`

## Linked artifacts

- [GitHub-friendly Mermaid preview](sample_graph_mermaid.md)
- [Mermaid source](sample_graph.mmd)
- [Graphviz DOT source](sample_graph.dot)
- [Report dashboard HTML](sample_graph_worker_comparison_report_dashboard.html)
- [Worker-limited schedule SVG (1 worker)](sample_graph_single_worker_schedule.svg)
- [Worker-limited schedule JSON (1 worker)](sample_graph_single_worker_schedule.json)
- [Worker-limited schedule SVG (2 workers)](sample_graph_2_workers_schedule.svg)
- [Worker-limited schedule JSON (2 workers)](sample_graph_2_workers_schedule.json)
- [Worker-limited schedule SVG (3 workers)](sample_graph_3_workers_schedule.svg)
- [Worker-limited schedule JSON (3 workers)](sample_graph_3_workers_schedule.json)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `lint, compile, package, unit, publish`
- widest parallel layer: `layer 2` with `2` task(s): `package`, `unit`
- non-critical slack budget available for schedule tradeoffs: `1` time units
- worker-limited dispatch uses critical-first, low-slack, longer-duration tie-breaking across `1 worker`
- worker cap increases makespan by `1` time unit(s) over the unlimited-layer bound of `8`
- utilization under the worker cap: `100.0%` with `0` idle worker-time unit(s)
- biggest queue delay: `package` waited `2` time unit(s) after becoming ready
- compared worker caps against the unlimited baseline of `8`: `1 worker → 9, 2 workers → 8, 3 workers → 8`

## Parallel layer windows

- Layer 0 (`0` → `1`): `lint`
- Layer 1 (`1` → `5`): `compile`
- Layer 2 (`5` → `7`): `package`, `unit`
- Layer 3 (`7` → `8`): `publish`

## Worker-capacity comparison

| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 worker | 9 | 1 | 9 | 100.0% | 0 | 1 | 2 |
| 2 workers | 8 | 0 | 8 | 56.2% | 7 | 0 | 0 |
| 3 workers | 8 | 0 | 8 | 37.5% | 15 | 0 | 0 |

## Worker-limited comparison

- Worker limit: `1`
- Strategy: `critical-first`
- Total work: `9`
- Theoretical lower bound: `9`
- Unlimited layered makespan: `8`
- Worker-limited makespan: `9`
- Dispatch order: `lint, compile, unit, package, publish`

### Worker timelines

- Worker 1 (`0 → 9`): lint (0→1), compile (1→5), unit (5→7), package (7→8), publish (8→9)

### Worker-limited task table

| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| lint | 1 | — | — | 0 | 0 | 1 | 0 | yes |
| compile | 1 | — | — | 1 | 1 | 5 | 0 | yes |
| unit | 1 | — | — | 5 | 5 | 7 | 0 | yes |
| package | 1 | — | — | 5 | 7 | 8 | 2 | no |
| publish | 1 | — | — | 8 | 8 | 9 | 0 | yes |

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| lint | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | ruff check . |
| compile | 1 | lint | 4 | — | 1 | 5 | 1 | 5 | 0 | yes | python -m build |
| package | 2 | compile | 1 | — | 5 | 6 | 6 | 7 | 1 | no | python -m zipapp |
| unit | 2 | compile | 2 | — | 5 | 7 | 5 | 7 | 0 | yes | pytest |
| publish | 3 | unit, package | 1 | — | 7 | 8 | 7 | 8 | 0 | yes | twine upload dist/* |

## Deterministic execution order

1. `lint`
   - Dependencies: `ready at start`
   - Window: `0 → 1`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `ruff check .`
2. `compile`
   - Dependencies: `lint`
   - Window: `1 → 5`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python -m build`
3. `package`
   - Dependencies: `compile`
   - Window: `5 → 6`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `python -m zipapp`
4. `unit`
   - Dependencies: `compile`
   - Window: `5 → 7`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `pytest`
5. `publish`
   - Dependencies: `unit`, `package`
   - Window: `7 → 8`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `twine upload dist/*`
