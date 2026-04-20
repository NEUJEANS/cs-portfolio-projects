# Dependency graph strategy benchmark suite

- Suite source: `projects/dependency-graph-planner/portfolio_benchmark_suite.json`
- Scenario count: `5`
- Strategies covered: `fifo, critical-first, longest-processing-time`

## Aggregate strategy scoreboard

| Strategy | Scenarios | Rank-1 finishes | Best-makespan finishes | Avg makespan | Avg Δ vs best | Avg total queue delay | Avg max queue delay | Avg utilization |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fifo | 5 | 4 | 4 | 10.00 | 0.60 | 3.00 | 3.00 | 55.2% |
| critical-first | 5 | 3 | 4 | 9.60 | 0.20 | 3.80 | 3.80 | 57.0% |
| longest-processing-time | 4 | 2 | 3 | 10.50 | 0.75 | 3.75 | 3.75 | 54.4% |

## Scenario — sample-2-workers

- Manifest: `sample_graph.json`
- Worker limit: `2 workers`
- Task count: `5`
- Unlimited makespan: `8`
- Best scenario makespan: `8` via `critical-first, fifo, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first, fifo, longest-processing-time`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 8 | 0 | 0 | 0 | 0 | 7 | 56.2% | lint, compile, unit, package, publish |
| 1 | fifo | 8 | 0 | 0 | 0 | 0 | 7 | 56.2% | lint, compile, package, unit, publish |
| 1 | longest-processing-time | 8 | 0 | 0 | 0 | 0 | 7 | 56.2% | lint, compile, unit, package, publish |

## Scenario — strategy-2-workers

- Manifest: `strategy_graph.json`
- Worker limit: `2 workers`
- Task count: `6`
- Unlimited makespan: `10`
- Best scenario makespan: `13` via `critical-first`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 13 | 3 | 0 | 6 | 6 | 4 | 84.6% | core-seed, alpha-long, core-stage-1, core-stage-2, beta-long, ship |
| 2 | fifo | 16 | 6 | 3 | 6 | 6 | 10 | 68.8% | alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship |
| 2 | longest-processing-time | 16 | 6 | 3 | 6 | 6 | 10 | 68.8% | alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship |

## Scenario — resource-3-workers

- Manifest: `resource_graph.json`
- Worker limit: `3 workers`
- Task count: `5`
- Unlimited makespan: `6`
- Best scenario makespan: `8` via `fifo, critical-first, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `gpu=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 8 | 2 | 0 | 2 | 2 | 13 | 45.8% | prep, docs, gpu-eval, gpu-train, package |
| 2 | critical-first | 8 | 2 | 0 | 4 | 4 | 13 | 45.8% | prep, gpu-train, docs, gpu-eval, package |
| 2 | longest-processing-time | 8 | 2 | 0 | 4 | 4 | 13 | 45.8% | prep, gpu-train, docs, gpu-eval, package |

## Scenario — multi-resource-3-workers

- Manifest: `multi_resource_graph.json`
- Worker limit: `3 workers`
- Task count: `6`
- Unlimited makespan: `7`
- Best scenario makespan: `10` via `critical-first, fifo, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first, fifo, longest-processing-time`
- Resource capacities: `browser-lab=2, gpu=1, signing=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 10 | 3 | 0 | 5 | 5 | 16 | 46.7% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |
| 1 | fifo | 10 | 3 | 0 | 5 | 5 | 16 | 46.7% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |
| 1 | longest-processing-time | 10 | 3 | 0 | 5 | 5 | 16 | 46.7% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |

## Scenario — multi-resource-browser-bump

- Manifest: `multi_resource_graph.json`
- Worker limit: `3 workers`
- Task count: `6`
- Unlimited makespan: `7`
- Best scenario makespan: `8` via `fifo`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `browser-lab=3, gpu=1, signing=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 8 | 1 | 0 | 2 | 2 | 10 | 58.3% | prep, browser-matrix, cross-platform-cert, gpu-train, sign, package |
| 2 | critical-first | 9 | 2 | 1 | 4 | 4 | 13 | 51.9% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |
