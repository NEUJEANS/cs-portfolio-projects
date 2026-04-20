# Dependency graph strategy benchmark suite

- Suite source: `projects/dependency-graph-planner/portfolio_benchmark_suite.json`
- Scenario count: `8`
- Strategies covered: `fifo, critical-first, longest-processing-time`

## Aggregate strategy scoreboard

| Strategy | Scenarios | Rank-1 finishes | Best-makespan finishes | Avg makespan | Avg Δ vs best | Avg total queue delay | Avg max queue delay | Avg utilization |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fifo | 8 | 7 | 7 | 13.75 | 0.38 | 4.00 | 2.88 | 50.4% |
| critical-first | 8 | 4 | 7 | 13.50 | 0.12 | 5.00 | 3.62 | 51.6% |
| longest-processing-time | 7 | 3 | 6 | 14.57 | 0.43 | 5.14 | 3.43 | 49.3% |

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

## Scenario — generated-ci-4-workers

- Manifest: `generated_ci_pipeline.json`
- Worker limit: `4 workers`
- Task count: `16`
- Unlimited makespan: `16`
- Best scenario makespan: `16` via `critical-first, fifo, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `critical-first, fifo, longest-processing-time`
- Resource capacities: `browser-lab=1, docker-builder=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | critical-first | 16 | 0 | 0 | 0 | 0 | 37 | 42.2% | checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-03, unit-shard-02, unit-shard-04, package-artifact, build-container, publish-preview-image, security-scan, deploy-preview, smoke-preview, promote-mainline |
| 1 | fifo | 16 | 0 | 0 | 0 | 0 | 37 | 42.2% | checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-02, unit-shard-03, unit-shard-04, package-artifact, build-container, publish-preview-image, security-scan, deploy-preview, smoke-preview, promote-mainline |
| 1 | longest-processing-time | 16 | 0 | 0 | 0 | 0 | 37 | 42.2% | checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-03, unit-shard-02, unit-shard-04, package-artifact, build-container, security-scan, publish-preview-image, deploy-preview, smoke-preview, promote-mainline |

## Scenario — generated-release-3-workers

- Manifest: `generated_release_pipeline.json`
- Worker limit: `3 workers`
- Task count: `19`
- Unlimited makespan: `21`
- Best scenario makespan: `24` via `fifo, longest-processing-time, critical-first`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `prod-slot=1, signing=1`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 24 | 3 | 0 | 5 | 3 | 42 | 41.7% | freeze-release-branch, assemble-release-notes, build-linux, build-macos, build-windows, sign-linux, sign-macos, sign-windows, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release |
| 2 | longest-processing-time | 24 | 3 | 0 | 7 | 3 | 42 | 41.7% | freeze-release-branch, build-macos, build-linux, build-windows, sign-linux, assemble-release-notes, sign-windows, sign-macos, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release |
| 3 | critical-first | 24 | 3 | 0 | 7 | 4 | 42 | 41.7% | freeze-release-branch, build-macos, build-linux, build-windows, sign-linux, assemble-release-notes, sign-macos, sign-windows, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release |

## Scenario — generated-data-pipeline-4-workers

- Manifest: `generated_data_pipeline.json`
- Worker limit: `4 workers`
- Task count: `16`
- Unlimited makespan: `15`
- Best scenario makespan: `20` via `fifo, critical-first, longest-processing-time`
- Rank-1 strategies after queue-delay tie-breaks: `fifo`
- Resource capacities: `gpu=1, warehouse=2`

| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | fifo | 20 | 5 | 0 | 12 | 5 | 45 | 43.8% | ingest-events, ingest-orders, ingest-payments, quality-profile, schema-validate, transform-partition-01, transform-partition-02, transform-partition-03, transform-partition-04, transform-partition-05, build-features, backfill-marts, train-model, publish-dashboard, publish-model, notify-ops |
| 2 | critical-first | 20 | 5 | 0 | 14 | 6 | 45 | 43.8% | ingest-events, ingest-orders, ingest-payments, schema-validate, quality-profile, transform-partition-01, transform-partition-03, transform-partition-05, transform-partition-02, transform-partition-04, build-features, train-model, backfill-marts, publish-dashboard, publish-model, notify-ops |
| 2 | longest-processing-time | 20 | 5 | 0 | 14 | 6 | 45 | 43.8% | ingest-events, ingest-orders, ingest-payments, quality-profile, schema-validate, transform-partition-01, transform-partition-03, transform-partition-05, transform-partition-02, transform-partition-04, build-features, train-model, backfill-marts, publish-dashboard, publish-model, notify-ops |
