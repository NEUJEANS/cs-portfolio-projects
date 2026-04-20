# Multi-resource release certification workflow

Release-engineering example where browser labs, GPU time, and a signing slot all act as renewable resources that can bottleneck certification and packaging.

- Source manifest: `projects/dependency-graph-planner/multi_resource_graph.json`
- Task count: `6`
- Parallel layers: `4`
- Estimated makespan: `7`
- Critical path: `prep -> browser-matrix -> package`
- Worker-limited makespan (3 workers): `10`
- Worker-limited strategy: `critical-first`

## Linked artifacts

- [GitHub-friendly Mermaid preview](multi_resource_graph_mermaid.md)
- [Mermaid source](multi_resource_graph.mmd)
- [Graphviz DOT source](multi_resource_graph.dot)
- [Report dashboard HTML](multi_resource_graph_report_dashboard.html)
- [Worker-limited schedule SVG](multi_resource_graph_3_workers_schedule.svg)
- [Worker-limited schedule JSON](multi_resource_graph_3_workers_schedule.json)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `prep, browser-matrix, cross-platform-cert, gpu-train, sign, package`
- widest parallel layer: `layer 1` with `3` task(s): `browser-matrix`, `cross-platform-cert`, `gpu-train`
- non-critical slack budget available for schedule tradeoffs: `5` time units
- worker-limited dispatch uses critical-first, low-slack, longer-duration tie-breaking across `3 workers`
- worker cap increases makespan by `3` time unit(s) over the unlimited-layer bound of `7`
- utilization under the worker cap: `46.7%` with `16` idle worker-time unit(s)
- biggest queue delay: `cross-platform-cert` waited `5` time unit(s) after becoming ready on `browser-lab#1 + gpu#1`
- renewable resource caps active for the constrained run: `browser-lab=2, gpu=1, signing=1`
- compared worker caps against the unlimited baseline of `7`: `3 workers → 10`

## Parallel layer windows

- Layer 0 (`0` → `1`): `prep`
- Layer 1 (`1` → `6`): `browser-matrix`, `cross-platform-cert`, `gpu-train`
- Layer 2 (`3` → `4`): `sign`
- Layer 3 (`6` → `7`): `package`

## Worker-capacity comparison

| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 workers | 10 | 3 | 7 | 46.7% | 16 | 1 | 5 |

## Worker-limited comparison

- Worker limit: `3`
- Strategy: `critical-first`
- Total work: `14`
- Theoretical lower bound: `7`
- Unlimited layered makespan: `7`
- Worker-limited makespan: `10`
- Dispatch order: `prep, browser-matrix, gpu-train, cross-platform-cert, sign, package`

### Worker timelines

- Worker 1 (`0 → 10`): prep (0→1), browser-matrix (1→6) [browser-lab#{1,2}], cross-platform-cert (6→8) [browser-lab#1 + gpu#1], sign (8→9) [signing#1], package (9→10)
- Worker 2 (`1 → 5`): gpu-train (1→5) [gpu#1]
- Worker 3: `idle for the full run`

### Resource-class utilization

| Resource class | Capacity | Tasks | Reserved units | Peak concurrent usage | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| browser-lab | 2 | 2 | 12 | 2 | 60.0% | 8 | 1 | 5 |
| gpu | 1 | 2 | 6 | 1 | 60.0% | 4 | 1 | 5 |
| signing | 1 | 1 | 1 | 1 | 10.0% | 9 | 0 | 0 |

### Worker-limited task table

| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| prep | 1 | — | — | 0 | 0 | 1 | 0 | yes |
| browser-matrix | 1 | browser-lab×2 | browser-lab#{1,2} | 1 | 1 | 6 | 0 | yes |
| gpu-train | 2 | gpu | gpu#1 | 1 | 1 | 5 | 0 | no |
| cross-platform-cert | 1 | browser-lab, gpu | browser-lab#1 + gpu#1 | 1 | 6 | 8 | 5 | no |
| sign | 1 | signing | signing#1 | 8 | 8 | 9 | 0 | no |
| package | 1 | — | — | 9 | 9 | 10 | 0 | yes |

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| prep | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | python tools/prepare_release.py |
| browser-matrix | 1 | prep | 5 | browser-lab×2 | 1 | 6 | 1 | 6 | 0 | yes | python tools/run_browser_matrix.py --workers 2 |
| cross-platform-cert | 1 | prep | 2 | browser-lab, gpu | 1 | 3 | 3 | 5 | 2 | no | python tools/certify_release.py |
| gpu-train | 1 | prep | 4 | gpu | 1 | 5 | 2 | 6 | 1 | no | python tools/train_model.py |
| sign | 2 | cross-platform-cert | 1 | signing | 3 | 4 | 5 | 6 | 2 | no | python tools/sign_release.py |
| package | 3 | browser-matrix, gpu-train, sign | 1 | — | 6 | 7 | 6 | 7 | 0 | yes | python tools/package_release.py |

## Deterministic execution order

1. `prep`
   - Dependencies: `ready at start`
   - Window: `0 → 1`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python tools/prepare_release.py`
2. `browser-matrix`
   - Dependencies: `prep`
   - Window: `1 → 6`
   - Slack: `0`
   - Resources: `browser-lab×2`
   - Command: `python tools/run_browser_matrix.py --workers 2`
3. `cross-platform-cert`
   - Dependencies: `prep`
   - Window: `1 → 3`
   - Slack: `2`
   - Resources: `browser-lab, gpu`
   - Command: `python tools/certify_release.py`
4. `gpu-train`
   - Dependencies: `prep`
   - Window: `1 → 5`
   - Slack: `1`
   - Resources: `gpu`
   - Command: `python tools/train_model.py`
5. `sign`
   - Dependencies: `cross-platform-cert`
   - Window: `3 → 4`
   - Slack: `2`
   - Resources: `signing`
   - Command: `python tools/sign_release.py`
6. `package`
   - Dependencies: `browser-matrix`, `gpu-train`, `sign`
   - Window: `6 → 7`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python tools/package_release.py`
