# Ready-queue strategy tradeoff demo

Compact benchmark graph that makes critical-first, FIFO, and longest-processing-time dispatch choices visibly diverge under the same worker cap.

- Source manifest: `projects/dependency-graph-planner/strategy_graph.json`
- Task count: `6`
- Parallel layers: `4`
- Estimated makespan: `10`
- Critical path: `core-seed -> core-stage-1 -> core-stage-2 -> ship`
- Worker-limited makespan (2 workers): `13`
- Worker-limited strategy: `critical-first`

## Linked artifacts

- [GitHub-friendly Mermaid preview](strategy_graph_mermaid.md)
- [Mermaid source](strategy_graph.mmd)
- [Graphviz DOT source](strategy_graph.dot)
- [Report dashboard HTML](strategy_graph_strategy_report_dashboard.html)
- [Worker-limited schedule SVG (2 workers, critical-first)](strategy_graph_2_workers_critical_first_schedule.svg)
- [Worker-limited schedule JSON (2 workers, critical-first)](strategy_graph_2_workers_critical_first_schedule.json)
- [Worker-limited schedule SVG (2 workers, fifo)](strategy_graph_2_workers_fifo_schedule.svg)
- [Worker-limited schedule JSON (2 workers, fifo)](strategy_graph_2_workers_fifo_schedule.json)
- [Worker-limited schedule SVG (2 workers, longest-processing-time)](strategy_graph_2_workers_longest_processing_time_schedule.svg)
- [Worker-limited schedule JSON (2 workers, longest-processing-time)](strategy_graph_2_workers_longest_processing_time_schedule.json)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship`
- widest parallel layer: `layer 0` with `3` task(s): `alpha-long`, `beta-long`, `core-seed`
- non-critical slack budget available for schedule tradeoffs: `6` time units
- worker-limited dispatch uses critical-first, low-slack, longer-duration tie-breaking across `2 workers`
- worker cap increases makespan by `3` time unit(s) over the unlimited-layer bound of `10`
- utilization under the worker cap: `84.6%` with `4` idle worker-time unit(s)
- biggest queue delay: `beta-long` waited `6` time unit(s) after becoming ready
- compared worker caps against the unlimited baseline of `10`: `2 workers → 13`
- compared scheduling strategies at `2 workers`: `critical-first → 13, fifo → 16, longest-processing-time → 16`

## Parallel layer windows

- Layer 0 (`0` → `6`): `alpha-long`, `beta-long`, `core-seed`
- Layer 1 (`1` → `5`): `core-stage-1`
- Layer 2 (`5` → `9`): `core-stage-2`
- Layer 3 (`9` → `10`): `ship`

## Worker-capacity comparison

| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 workers | 13 | 3 | 11 | 84.6% | 4 | 1 | 6 |

## Scheduling-strategy comparison

| Strategy | Makespan | Δ vs unlimited | Δ vs primary strategy | Delayed tasks | Max queue delay | Dispatch order |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| critical-first | 13 | 3 | 0 | 1 | 6 | core-seed, alpha-long, core-stage-1, core-stage-2, beta-long, ship |
| fifo | 16 | 6 | 3 | 1 | 6 | alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship |
| longest-processing-time | 16 | 6 | 3 | 1 | 6 | alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship |

## Worker-limited comparison

- Worker limit: `2`
- Strategy: `critical-first`
- Total work: `22`
- Theoretical lower bound: `11`
- Unlimited layered makespan: `10`
- Worker-limited makespan: `13`
- Dispatch order: `core-seed, alpha-long, core-stage-1, core-stage-2, beta-long, ship`

### Worker timelines

- Worker 1 (`0 → 13`): core-seed (0→1), core-stage-1 (1→5), core-stage-2 (5→9), ship (12→13)
- Worker 2 (`0 → 12`): alpha-long (0→6), beta-long (6→12)

### Worker-limited task table

| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| core-seed | 1 | — | — | 0 | 0 | 1 | 0 | yes |
| alpha-long | 2 | — | — | 0 | 0 | 6 | 0 | no |
| core-stage-1 | 1 | — | — | 1 | 1 | 5 | 0 | yes |
| core-stage-2 | 1 | — | — | 5 | 5 | 9 | 0 | yes |
| beta-long | 2 | — | — | 0 | 6 | 12 | 6 | no |
| ship | 1 | — | — | 12 | 12 | 13 | 0 | yes |

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| alpha-long | 0 | — | 6 | — | 0 | 6 | 3 | 9 | 3 | no | — |
| beta-long | 0 | — | 6 | — | 0 | 6 | 3 | 9 | 3 | no | — |
| core-seed | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | — |
| core-stage-1 | 1 | core-seed | 4 | — | 1 | 5 | 1 | 5 | 0 | yes | — |
| core-stage-2 | 2 | core-stage-1 | 4 | — | 5 | 9 | 5 | 9 | 0 | yes | — |
| ship | 3 | alpha-long, beta-long, core-stage-2 | 1 | — | 9 | 10 | 9 | 10 | 0 | yes | — |

## Deterministic execution order

1. `alpha-long`
   - Dependencies: `ready at start`
   - Window: `0 → 6`
   - Slack: `3`
   - Resources: `generic worker`
   - Command: `documentation only`
2. `beta-long`
   - Dependencies: `ready at start`
   - Window: `0 → 6`
   - Slack: `3`
   - Resources: `generic worker`
   - Command: `documentation only`
3. `core-seed`
   - Dependencies: `ready at start`
   - Window: `0 → 1`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `documentation only`
4. `core-stage-1`
   - Dependencies: `core-seed`
   - Window: `1 → 5`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `documentation only`
5. `core-stage-2`
   - Dependencies: `core-stage-1`
   - Window: `5 → 9`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `documentation only`
6. `ship`
   - Dependencies: `alpha-long`, `beta-long`, `core-stage-2`
   - Window: `9 → 10`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `documentation only`
