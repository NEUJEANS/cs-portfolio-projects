# Dependency graph strategy benchmark suite

- Suite source: `projects/dependency-graph-planner/portfolio_benchmark_suite.json`
- Scenario count: `11`
- Strategies covered: `critical-first, fifo, longest-processing-time`
- Aggregate leader: `critical-first`
- Stochastic uncertainty scenarios: `3`

## Linked artifacts

- [Benchmark dashboard HTML](portfolio_benchmark_suite_report_dashboard.html)
- [Benchmark JSON snapshot](portfolio_benchmark_suite_report.json)
- [Aggregate strategy CSV](portfolio_benchmark_suite_aggregates.csv)
- [Per-scenario strategy CSV](portfolio_benchmark_suite_strategies.csv)

## Aggregate strategy scoreboard

| Strategy | Scenarios | Rank-1 finishes | Best-makespan finishes | Avg makespan | Avg Δ vs critical path | Avg ratio vs critical path | Avg Δ vs best | Avg total queue delay | Avg max queue delay | Avg utilization |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| critical-first | 11 | 7 | 10 | 17.18 | 3.18 | 1.24× | 0.09 | 20.91 | 8.27 | 63.4% |
| fifo | 11 | 7 | 7 | 18.91 | 4.91 | 1.33× | 1.82 | 11.91 | 4.73 | 58.1% |
| longest-processing-time | 10 | 3 | 6 | 19.80 | 5.10 | 1.33× | 1.80 | 13.70 | 5.60 | 58.5% |

## Aggregate stochastic robustness

| Strategy | Stochastic scenarios | Avg sampled makespan | Avg p50 | Avg p90 | Avg worst-case | Avg Δ vs sampled critical path | Avg ratio vs sampled critical path | Avg Δ vs sampled best | Avg sampled best-finish rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| critical-first | 3 | 31.54 | 31.33 | 33.33 | 36.67 | 6.68 | 1.27× | 0.00 | 100.0% |
| longest-processing-time | 3 | 38.05 | 38.00 | 41.33 | 44.33 | 13.19 | 1.53× | 6.51 | 0.0% |
| fifo | 3 | 38.16 | 38.00 | 41.33 | 43.67 | 13.30 | 1.54× | 6.62 | 0.0% |

## Scenario — sample-2-workers

- Manifest: `sample_graph.json`
- Worker limit: `2 workers`
- Task count: `5`
- Unlimited makespan: `8`
- Critical-path lower bound: `8`
- Best scenario makespan: `8` via `critical-first, fifo, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first, fifo, longest-processing-time`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 8 | 0 | 0 | 1.00× | 0 | 0 | 0 | 7 | 56.2% | lint, compile, unit, package, publish |
| 1 | fifo | 8 | 0 | 0 | 1.00× | 0 | 0 | 0 | 7 | 56.2% | lint, compile, package, unit, publish |
| 1 | longest-processing-time | 8 | 0 | 0 | 1.00× | 0 | 0 | 0 | 7 | 56.2% | lint, compile, unit, package, publish |

## Scenario — strategy-2-workers

- Manifest: `strategy_graph.json`
- Worker limit: `2 workers`
- Task count: `6`
- Unlimited makespan: `10`
- Critical-path lower bound: `10`
- Best scenario makespan: `13` via `critical-first`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 13 | 3 | 3 | 1.30× | 0 | 6 | 6 | 4 | 84.6% | core-seed, alpha-long, core-stage-1, core-stage-2, beta-long, ship |
| 2 | fifo | 16 | 6 | 6 | 1.60× | 3 | 6 | 6 | 10 | 68.8% | alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship |
| 2 | longest-processing-time | 16 | 6 | 6 | 1.60× | 3 | 6 | 6 | 10 | 68.8% | alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship |

## Scenario — resource-3-workers

- Manifest: `resource_graph.json`
- Worker limit: `3 workers`
- Task count: `5`
- Unlimited makespan: `6`
- Critical-path lower bound: `6`
- Best scenario makespan: `8` via `fifo, critical-first, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `gpu=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 8 | 2 | 2 | 1.33× | 0 | 2 | 2 | 13 | 45.8% | prep, docs, gpu-eval, gpu-train, package |
| 2 | critical-first | 8 | 2 | 2 | 1.33× | 0 | 4 | 4 | 13 | 45.8% | prep, gpu-train, docs, gpu-eval, package |
| 2 | longest-processing-time | 8 | 2 | 2 | 1.33× | 0 | 4 | 4 | 13 | 45.8% | prep, gpu-train, docs, gpu-eval, package |

## Scenario — multi-resource-3-workers

- Manifest: `multi_resource_graph.json`
- Worker limit: `3 workers`
- Task count: `6`
- Unlimited makespan: `7`
- Critical-path lower bound: `7`
- Best scenario makespan: `10` via `critical-first, fifo, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first, fifo, longest-processing-time`
- Resource capacities: `browser-lab=2, gpu=1, signing=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 10 | 3 | 3 | 1.43× | 0 | 5 | 5 | 16 | 46.7% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |
| 1 | fifo | 10 | 3 | 3 | 1.43× | 0 | 5 | 5 | 16 | 46.7% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |
| 1 | longest-processing-time | 10 | 3 | 3 | 1.43× | 0 | 5 | 5 | 16 | 46.7% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |

## Scenario — multi-resource-browser-bump

- Manifest: `multi_resource_graph.json`
- Worker limit: `3 workers`
- Task count: `6`
- Unlimited makespan: `7`
- Critical-path lower bound: `7`
- Best scenario makespan: `8` via `fifo`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `browser-lab=3, gpu=1, signing=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 8 | 1 | 1 | 1.14× | 0 | 2 | 2 | 10 | 58.3% | prep, browser-matrix, cross-platform-cert, gpu-train, sign, package |
| 2 | critical-first | 9 | 2 | 2 | 1.29× | 1 | 4 | 4 | 13 | 51.9% | prep, browser-matrix, gpu-train, cross-platform-cert, sign, package |

## Scenario — generated-ci-4-workers

- Manifest: `generated_ci_pipeline.json`
- Worker limit: `4 workers`
- Task count: `16`
- Unlimited makespan: `16`
- Critical-path lower bound: `16`
- Best scenario makespan: `16` via `critical-first, fifo, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first, fifo, longest-processing-time`
- Resource capacities: `browser-lab=1, docker-builder=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 16 | 0 | 0 | 1.00× | 0 | 0 | 0 | 37 | 42.2% | checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-03, unit-shard-02, unit-shard-04, package-artifact, build-container, publish-preview-image, security-scan, deploy-preview, smoke-preview, promote-mainline |
| 1 | fifo | 16 | 0 | 0 | 1.00× | 0 | 0 | 0 | 37 | 42.2% | checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-02, unit-shard-03, unit-shard-04, package-artifact, build-container, publish-preview-image, security-scan, deploy-preview, smoke-preview, promote-mainline |
| 1 | longest-processing-time | 16 | 0 | 0 | 1.00× | 0 | 0 | 0 | 37 | 42.2% | checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-03, unit-shard-02, unit-shard-04, package-artifact, build-container, security-scan, publish-preview-image, deploy-preview, smoke-preview, promote-mainline |

## Scenario — generated-release-3-workers

- Manifest: `generated_release_pipeline.json`
- Worker limit: `3 workers`
- Task count: `19`
- Unlimited makespan: `21`
- Critical-path lower bound: `21`
- Best scenario makespan: `24` via `fifo, longest-processing-time, critical-first`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `prod-slot=1, signing=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 24 | 3 | 3 | 1.14× | 0 | 5 | 3 | 42 | 41.7% | freeze-release-branch, assemble-release-notes, build-linux, build-macos, build-windows, sign-linux, sign-macos, sign-windows, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release |
| 2 | longest-processing-time | 24 | 3 | 3 | 1.14× | 0 | 7 | 3 | 42 | 41.7% | freeze-release-branch, build-macos, build-linux, build-windows, sign-linux, assemble-release-notes, sign-windows, sign-macos, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release |
| 3 | critical-first | 24 | 3 | 3 | 1.14× | 0 | 7 | 4 | 42 | 41.7% | freeze-release-branch, build-macos, build-linux, build-windows, sign-linux, assemble-release-notes, sign-macos, sign-windows, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release |

## Scenario — generated-data-pipeline-4-workers

- Manifest: `generated_data_pipeline.json`
- Worker limit: `4 workers`
- Task count: `16`
- Unlimited makespan: `15`
- Critical-path lower bound: `15`
- Best scenario makespan: `20` via `fifo, critical-first, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `gpu=1, warehouse=2`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 20 | 5 | 5 | 1.33× | 0 | 12 | 5 | 45 | 43.8% | ingest-events, ingest-orders, ingest-payments, quality-profile, schema-validate, transform-partition-01, transform-partition-02, transform-partition-03, transform-partition-04, transform-partition-05, build-features, backfill-marts, train-model, publish-dashboard, publish-model, notify-ops |
| 2 | critical-first | 20 | 5 | 5 | 1.33× | 0 | 14 | 6 | 45 | 43.8% | ingest-events, ingest-orders, ingest-payments, schema-validate, quality-profile, transform-partition-01, transform-partition-03, transform-partition-05, transform-partition-02, transform-partition-04, build-features, train-model, backfill-marts, publish-dashboard, publish-model, notify-ops |
| 2 | longest-processing-time | 20 | 5 | 5 | 1.33× | 0 | 14 | 6 | 45 | 43.8% | ingest-events, ingest-orders, ingest-payments, quality-profile, schema-validate, transform-partition-01, transform-partition-03, transform-partition-05, transform-partition-02, transform-partition-04, build-features, train-model, backfill-marts, publish-dashboard, publish-model, notify-ops |

## Scenario — generated-stress-seed17-2-workers

- Manifest: `generated_stress_seed17.json`
- Worker limit: `2 workers`
- Task count: `16`
- Unlimited makespan: `22`
- Critical-path lower bound: `22`
- Best scenario makespan: `28` via `critical-first`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first`
- Stochastic duration simulation: `64 triangular samples (seed 20260420, factors 0.70×/1.00×/1.80×)`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 28 | 6 | 6 | 1.27× | 0 | 68 | 22 | 2 | 96.4% | seed, bulk-01, critical-chain-01, critical-chain-02, bulk-04, critical-chain-03, critical-chain-04, bulk-02, critical-chain-05, follow-up-02, critical-chain-06, bulk-05, follow-up-01, bulk-03, follow-up-03, ship |
| 2 | fifo | 33 | 11 | 11 | 1.50× | 5 | 33 | 11 | 12 | 81.8% | bulk-01, bulk-02, bulk-03, bulk-04, bulk-05, seed, critical-chain-01, follow-up-03, critical-chain-02, follow-up-01, critical-chain-03, critical-chain-04, follow-up-02, critical-chain-05, critical-chain-06, ship |
| 2 | longest-processing-time | 33 | 11 | 11 | 1.50× | 5 | 33 | 11 | 12 | 81.8% | bulk-01, bulk-04, bulk-02, bulk-03, bulk-05, seed, critical-chain-01, follow-up-03, critical-chain-02, follow-up-01, critical-chain-03, critical-chain-04, follow-up-02, critical-chain-05, critical-chain-06, ship |

### Stochastic robustness

| Strategy | Avg sampled makespan | P50 | P90 | Worst-case | Avg Δ vs sampled critical path | Avg ratio vs sampled critical path | Avg Δ vs sampled best | Best-finish rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| critical-first | 33.39 | 33 | 35 | 38 | 7.80 | 1.31× | 0.00 | 100.0% (64/64) |
| fifo | 39.00 | 39 | 42 | 45 | 13.41 | 1.53× | 5.61 | 0.0% (0/64) |
| longest-processing-time | 39.97 | 40 | 43 | 47 | 14.38 | 1.56× | 6.58 | 0.0% (0/64) |

## Scenario — generated-stress-seed29-2-workers

- Manifest: `generated_stress_seed29.json`
- Worker limit: `2 workers`
- Task count: `16`
- Unlimited makespan: `20`
- Critical-path lower bound: `20`
- Best scenario makespan: `25` via `critical-first`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first`
- Stochastic duration simulation: `64 triangular samples (seed 20260420, factors 0.70×/1.00×/1.80×)`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 25 | 5 | 5 | 1.25× | 0 | 61 | 19 | 4 | 92.0% | seed, bulk-01, critical-chain-01, bulk-03, critical-chain-02, critical-chain-03, bulk-04, critical-chain-04, follow-up-03, critical-chain-05, bulk-02, critical-chain-06, bulk-05, follow-up-01, follow-up-02, ship |
| 2 | longest-processing-time | 30 | 10 | 10 | 1.50× | 5 | 35 | 10 | 14 | 76.7% | bulk-03, bulk-02, bulk-05, bulk-01, bulk-04, seed, critical-chain-01, follow-up-03, critical-chain-02, follow-up-01, follow-up-02, critical-chain-03, critical-chain-04, critical-chain-05, critical-chain-06, ship |
| 3 | fifo | 32 | 12 | 12 | 1.60× | 7 | 34 | 8 | 18 | 71.9% | bulk-01, bulk-02, bulk-03, bulk-04, bulk-05, seed, follow-up-01, follow-up-02, follow-up-03, critical-chain-01, critical-chain-02, critical-chain-03, critical-chain-04, critical-chain-05, critical-chain-06, ship |

### Stochastic robustness

| Strategy | Avg sampled makespan | P50 | P90 | Worst-case | Avg Δ vs sampled critical path | Avg ratio vs sampled critical path | Avg Δ vs sampled best | Best-finish rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| critical-first | 28.20 | 28 | 30 | 33 | 4.86 | 1.21× | 0.00 | 100.0% (64/64) |
| longest-processing-time | 35.17 | 35 | 39 | 42 | 11.83 | 1.51× | 6.97 | 0.0% (0/64) |
| fifo | 36.52 | 36 | 40 | 42 | 13.17 | 1.57× | 8.31 | 0.0% (0/64) |

## Scenario — generated-stress-seed41-2-workers

- Manifest: `generated_stress_seed41.json`
- Worker limit: `2 workers`
- Task count: `16`
- Unlimited makespan: `22`
- Critical-path lower bound: `22`
- Best scenario makespan: `28` via `critical-first`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first`
- Stochastic duration simulation: `64 triangular samples (seed 20260420, factors 0.70×/1.00×/1.80×)`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 28 | 6 | 6 | 1.27× | 0 | 61 | 21 | 2 | 96.4% | seed, bulk-02, critical-chain-01, critical-chain-02, bulk-05, critical-chain-03, critical-chain-04, follow-up-03, bulk-03, critical-chain-05, follow-up-02, critical-chain-06, bulk-01, bulk-04, follow-up-01, ship |
| 2 | fifo | 33 | 11 | 11 | 1.50× | 5 | 32 | 10 | 12 | 81.8% | bulk-01, bulk-02, bulk-03, bulk-04, bulk-05, seed, follow-up-01, critical-chain-01, critical-chain-02, follow-up-03, critical-chain-03, critical-chain-04, follow-up-02, critical-chain-05, critical-chain-06, ship |
| 3 | longest-processing-time | 33 | 11 | 11 | 1.50× | 5 | 33 | 11 | 12 | 81.8% | bulk-05, bulk-01, bulk-02, bulk-03, bulk-04, seed, critical-chain-01, follow-up-01, critical-chain-02, follow-up-03, critical-chain-03, critical-chain-04, follow-up-02, critical-chain-05, critical-chain-06, ship |

### Stochastic robustness

| Strategy | Avg sampled makespan | P50 | P90 | Worst-case | Avg Δ vs sampled critical path | Avg ratio vs sampled critical path | Avg Δ vs sampled best | Best-finish rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| critical-first | 33.02 | 33 | 35 | 39 | 7.39 | 1.29× | 0.00 | 100.0% (64/64) |
| fifo | 38.95 | 39 | 42 | 44 | 13.33 | 1.52× | 5.94 | 0.0% (0/64) |
| longest-processing-time | 39.00 | 39 | 42 | 44 | 13.38 | 1.53× | 5.98 | 0.0% (0/64) |
