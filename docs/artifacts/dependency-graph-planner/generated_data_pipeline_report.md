# Dependency graph walkthrough — Generated Data Pipeline

- Source manifest: `projects/dependency-graph-planner/generated_data_pipeline.json`
- Task count: `16`
- Parallel layers: `7`
- Estimated makespan: `15`
- Critical path: `ingest-events -> schema-validate -> transform-partition-01 -> build-features -> train-model -> publish-model -> notify-ops`
- Worker-limited makespan (4 workers): `20`
- Worker-limited strategy: `critical-first`

## Linked artifacts

- [GitHub-friendly Mermaid preview](generated_data_pipeline_mermaid.md)
- [Mermaid source](generated_data_pipeline.mmd)
- [Graphviz DOT source](generated_data_pipeline.dot)
- [Report dashboard HTML](generated_data_pipeline_report_dashboard.html)
- [Worker-limited schedule SVG](generated_data_pipeline_4_workers_schedule.svg)
- [Worker-limited schedule JSON](generated_data_pipeline_4_workers_schedule.json)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `ingest-events, ingest-orders, ingest-payments, quality-profile, schema-validate, transform-partition-01, transform-partition-02, transform-partition-03, transform-partition-04, transform-partition-05, build-features, backfill-marts, publish-dashboard, train-model, publish-model, notify-ops`
- widest parallel layer: `layer 2` with `5` task(s): `transform-partition-01`, `transform-partition-02`, `transform-partition-03`, `transform-partition-04`, `transform-partition-05`
- non-critical slack budget available for schedule tradeoffs: `6` time units
- worker-limited dispatch uses critical-first, low-slack, longer-duration tie-breaking across `4 workers`
- worker cap increases makespan by `5` time unit(s) over the unlimited-layer bound of `15`
- utilization under the worker cap: `43.8%` with `45` idle worker-time unit(s)
- biggest queue delay: `transform-partition-04` waited `6` time unit(s) after becoming ready on `warehouse#1`
- renewable resource caps active for the constrained run: `gpu=1, warehouse=2`
- compared worker caps against the unlimited baseline of `15`: `4 workers → 20`

## Parallel layer windows

- Layer 0 (`0` → `2`): `ingest-events`, `ingest-orders`, `ingest-payments`
- Layer 1 (`2` → `4`): `quality-profile`, `schema-validate`
- Layer 2 (`3` → `6`): `transform-partition-01`, `transform-partition-02`, `transform-partition-03`, `transform-partition-04`, `transform-partition-05`
- Layer 3 (`6` → `9`): `build-features`
- Layer 4 (`9` → `13`): `backfill-marts`, `train-model`
- Layer 5 (`12` → `14`): `publish-dashboard`, `publish-model`
- Layer 6 (`14` → `15`): `notify-ops`

## Worker-capacity comparison

| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 workers | 20 | 5 | 15 | 43.8% | 45 | 4 | 6 |

## Worker-limited comparison

- Worker limit: `4`
- Strategy: `critical-first`
- Total work: `35`
- Theoretical lower bound: `15`
- Unlimited layered makespan: `15`
- Worker-limited makespan: `20`
- Dispatch order: `ingest-events, ingest-orders, ingest-payments, schema-validate, quality-profile, transform-partition-01, transform-partition-03, transform-partition-05, transform-partition-02, transform-partition-04, build-features, train-model, backfill-marts, publish-dashboard, publish-model, notify-ops`

### Worker timelines

- Worker 1 (`0 → 20`): ingest-events (0→2), schema-validate (2→3), transform-partition-01 (3→6) [warehouse#2], transform-partition-05 (6→9) [warehouse#2], transform-partition-04 (9→11) [warehouse#1], build-features (11→14) [warehouse#{1,2}], train-model (14→18) [gpu#1], publish-model (18→19), notify-ops (19→20)
- Worker 2 (`0 → 18`): ingest-orders (0→2), quality-profile (2→4) [warehouse#1], transform-partition-03 (4→7) [warehouse#1], transform-partition-02 (7→9) [warehouse#1], backfill-marts (14→17) [warehouse#1], publish-dashboard (17→18)
- Worker 3 (`0 → 2`): ingest-payments (0→2)
- Worker 4: `idle for the full run`

### Resource-class utilization

| Resource class | Capacity | Tasks | Reserved units | Peak concurrent usage | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gpu | 1 | 1 | 4 | 1 | 20.0% | 16 | 0 | 0 |
| warehouse | 2 | 8 | 24 | 2 | 60.0% | 16 | 4 | 6 |

### Worker-limited task table

| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| ingest-events | 1 | — | — | 0 | 0 | 2 | 0 | yes |
| ingest-orders | 2 | — | — | 0 | 0 | 2 | 0 | yes |
| ingest-payments | 3 | — | — | 0 | 0 | 2 | 0 | yes |
| schema-validate | 1 | — | — | 2 | 2 | 3 | 0 | yes |
| quality-profile | 2 | warehouse | warehouse#1 | 2 | 2 | 4 | 0 | no |
| transform-partition-01 | 1 | warehouse | warehouse#2 | 3 | 3 | 6 | 0 | yes |
| transform-partition-03 | 2 | warehouse | warehouse#1 | 3 | 4 | 7 | 1 | yes |
| transform-partition-05 | 1 | warehouse | warehouse#2 | 3 | 6 | 9 | 3 | yes |
| transform-partition-02 | 2 | warehouse | warehouse#1 | 3 | 7 | 9 | 4 | no |
| transform-partition-04 | 1 | warehouse | warehouse#1 | 3 | 9 | 11 | 6 | no |
| build-features | 1 | warehouse×2 | warehouse#{1,2} | 11 | 11 | 14 | 0 | yes |
| train-model | 1 | gpu | gpu#1 | 14 | 14 | 18 | 0 | yes |
| backfill-marts | 2 | warehouse | warehouse#1 | 14 | 14 | 17 | 0 | no |
| publish-dashboard | 2 | — | — | 17 | 17 | 18 | 0 | no |
| publish-model | 1 | — | — | 18 | 18 | 19 | 0 | yes |
| notify-ops | 1 | — | — | 19 | 19 | 20 | 0 | yes |

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| ingest-events | 0 | — | 2 | — | 0 | 2 | 0 | 2 | 0 | yes | spark-submit jobs/ingest_events.py |
| ingest-orders | 0 | — | 2 | — | 0 | 2 | 0 | 2 | 0 | yes | spark-submit jobs/ingest_orders.py |
| ingest-payments | 0 | — | 2 | — | 0 | 2 | 0 | 2 | 0 | yes | spark-submit jobs/ingest_payments.py |
| quality-profile | 1 | ingest-orders, ingest-events, ingest-payments | 2 | warehouse | 2 | 4 | 4 | 6 | 2 | no | dbt run --select quality_profile |
| schema-validate | 1 | ingest-orders, ingest-events, ingest-payments | 1 | — | 2 | 3 | 2 | 3 | 0 | yes | great_expectations checkpoint run bronze |
| transform-partition-01 | 2 | schema-validate | 3 | warehouse | 3 | 6 | 3 | 6 | 0 | yes | dbt run --select fact_orders_partition_1 |
| transform-partition-02 | 2 | schema-validate | 2 | warehouse | 3 | 5 | 4 | 6 | 1 | no | dbt run --select fact_orders_partition_2 |
| transform-partition-03 | 2 | schema-validate | 3 | warehouse | 3 | 6 | 3 | 6 | 0 | yes | dbt run --select fact_orders_partition_3 |
| transform-partition-04 | 2 | schema-validate | 2 | warehouse | 3 | 5 | 4 | 6 | 1 | no | dbt run --select fact_orders_partition_4 |
| transform-partition-05 | 2 | schema-validate | 3 | warehouse | 3 | 6 | 3 | 6 | 0 | yes | dbt run --select fact_orders_partition_5 |
| build-features | 3 | quality-profile, transform-partition-01, transform-partition-02, transform-partition-03, transform-partition-04, transform-partition-05 | 3 | warehouse×2 | 6 | 9 | 6 | 9 | 0 | yes | dbt run --select feature_store |
| backfill-marts | 4 | build-features | 3 | warehouse | 9 | 12 | 10 | 13 | 1 | no | dbt run --select marts.fct_revenue |
| publish-dashboard | 5 | backfill-marts | 1 | — | 12 | 13 | 13 | 14 | 1 | no | python jobs/publish_dashboard.py |
| train-model | 4 | build-features | 4 | gpu | 9 | 13 | 9 | 13 | 0 | yes | python jobs/train_model.py |
| publish-model | 5 | train-model | 1 | — | 13 | 14 | 13 | 14 | 0 | yes | python jobs/register_model.py |
| notify-ops | 6 | publish-dashboard, publish-model | 1 | — | 14 | 15 | 14 | 15 | 0 | yes | python jobs/notify_ops.py |

## Deterministic execution order

1. `ingest-events`
   - Dependencies: `ready at start`
   - Window: `0 → 2`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `spark-submit jobs/ingest_events.py`
2. `ingest-orders`
   - Dependencies: `ready at start`
   - Window: `0 → 2`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `spark-submit jobs/ingest_orders.py`
3. `ingest-payments`
   - Dependencies: `ready at start`
   - Window: `0 → 2`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `spark-submit jobs/ingest_payments.py`
4. `quality-profile`
   - Dependencies: `ingest-orders`, `ingest-events`, `ingest-payments`
   - Window: `2 → 4`
   - Slack: `2`
   - Resources: `warehouse`
   - Command: `dbt run --select quality_profile`
5. `schema-validate`
   - Dependencies: `ingest-orders`, `ingest-events`, `ingest-payments`
   - Window: `2 → 3`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `great_expectations checkpoint run bronze`
6. `transform-partition-01`
   - Dependencies: `schema-validate`
   - Window: `3 → 6`
   - Slack: `0`
   - Resources: `warehouse`
   - Command: `dbt run --select fact_orders_partition_1`
7. `transform-partition-02`
   - Dependencies: `schema-validate`
   - Window: `3 → 5`
   - Slack: `1`
   - Resources: `warehouse`
   - Command: `dbt run --select fact_orders_partition_2`
8. `transform-partition-03`
   - Dependencies: `schema-validate`
   - Window: `3 → 6`
   - Slack: `0`
   - Resources: `warehouse`
   - Command: `dbt run --select fact_orders_partition_3`
9. `transform-partition-04`
   - Dependencies: `schema-validate`
   - Window: `3 → 5`
   - Slack: `1`
   - Resources: `warehouse`
   - Command: `dbt run --select fact_orders_partition_4`
10. `transform-partition-05`
   - Dependencies: `schema-validate`
   - Window: `3 → 6`
   - Slack: `0`
   - Resources: `warehouse`
   - Command: `dbt run --select fact_orders_partition_5`
11. `build-features`
   - Dependencies: `quality-profile`, `transform-partition-01`, `transform-partition-02`, `transform-partition-03`, `transform-partition-04`, `transform-partition-05`
   - Window: `6 → 9`
   - Slack: `0`
   - Resources: `warehouse×2`
   - Command: `dbt run --select feature_store`
12. `backfill-marts`
   - Dependencies: `build-features`
   - Window: `9 → 12`
   - Slack: `1`
   - Resources: `warehouse`
   - Command: `dbt run --select marts.fct_revenue`
13. `publish-dashboard`
   - Dependencies: `backfill-marts`
   - Window: `12 → 13`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `python jobs/publish_dashboard.py`
14. `train-model`
   - Dependencies: `build-features`
   - Window: `9 → 13`
   - Slack: `0`
   - Resources: `gpu`
   - Command: `python jobs/train_model.py`
15. `publish-model`
   - Dependencies: `train-model`
   - Window: `13 → 14`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python jobs/register_model.py`
16. `notify-ops`
   - Dependencies: `publish-dashboard`, `publish-model`
   - Window: `14 → 15`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python jobs/notify_ops.py`
