# Synthetic CI pipeline (4 unit-test shards)

GitHub Actions style fan-out/fan-in workflow with artifact packaging, image publish, preview deploy, and smoke coverage.

- Source manifest: `projects/dependency-graph-planner/generated_ci_pipeline.json`
- Task count: `16`
- Parallel layers: `10`
- Estimated makespan: `16`
- Critical path: `checkout -> install-deps -> build-app -> unit-shard-01 -> package-artifact -> build-container -> publish-preview-image -> deploy-preview -> smoke-preview -> promote-mainline`
- Worker-limited makespan (4 workers): `16`
- Worker-limited strategy: `critical-first`

## Linked artifacts

- [GitHub-friendly Mermaid preview](generated_ci_pipeline_mermaid.md)
- [Mermaid source](generated_ci_pipeline.mmd)
- [Graphviz DOT source](generated_ci_pipeline.dot)
- [Report dashboard HTML](generated_ci_pipeline_report_dashboard.html)
- [Worker-limited schedule SVG](generated_ci_pipeline_4_workers_schedule.svg)
- [Worker-limited schedule JSON](generated_ci_pipeline_4_workers_schedule.json)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-02, unit-shard-03, unit-shard-04, package-artifact, build-container, publish-preview-image, deploy-preview, security-scan, smoke-preview, promote-mainline`
- widest parallel layer: `layer 3` with `4` task(s): `unit-shard-01`, `unit-shard-02`, `unit-shard-03`, `unit-shard-04`
- non-critical slack budget available for schedule tradeoffs: `12` time units
- worker-limited dispatch uses critical-first, low-slack, longer-duration tie-breaking across `4 workers`
- worker cap increases makespan by `0` time unit(s) over the unlimited-layer bound of `16`
- utilization under the worker cap: `42.2%` with `37` idle worker-time unit(s)
- renewable resource caps active for the constrained run: `browser-lab=1, docker-builder=1`
- compared worker caps against the unlimited baseline of `16`: `4 workers → 16`

## Parallel layer windows

- Layer 0 (`0` → `1`): `checkout`
- Layer 1 (`1` → `3`): `install-deps`
- Layer 2 (`3` → `5`): `build-app`, `lint`, `typecheck`
- Layer 3 (`5` → `8`): `unit-shard-01`, `unit-shard-02`, `unit-shard-03`, `unit-shard-04`
- Layer 4 (`8` → `9`): `package-artifact`
- Layer 5 (`9` → `11`): `build-container`
- Layer 6 (`11` → `13`): `publish-preview-image`, `security-scan`
- Layer 7 (`12` → `13`): `deploy-preview`
- Layer 8 (`13` → `15`): `smoke-preview`
- Layer 9 (`15` → `16`): `promote-mainline`

## Worker-capacity comparison

| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 workers | 16 | 0 | 16 | 42.2% | 37 | 0 | 0 |

## Worker-limited comparison

- Worker limit: `4`
- Strategy: `critical-first`
- Total work: `27`
- Theoretical lower bound: `16`
- Unlimited layered makespan: `16`
- Worker-limited makespan: `16`
- Dispatch order: `checkout, install-deps, build-app, lint, typecheck, unit-shard-01, unit-shard-03, unit-shard-02, unit-shard-04, package-artifact, build-container, publish-preview-image, security-scan, deploy-preview, smoke-preview, promote-mainline`

### Worker timelines

- Worker 1 (`0 → 16`): checkout (0→1), install-deps (1→3), build-app (3→5), unit-shard-01 (5→8), package-artifact (8→9), build-container (9→11) [docker-builder#1], publish-preview-image (11→12) [docker-builder#1], deploy-preview (12→13), smoke-preview (13→15) [browser-lab#1], promote-mainline (15→16)
- Worker 2 (`3 → 13`): lint (3→4), unit-shard-03 (5→8), security-scan (11→13)
- Worker 3 (`3 → 7`): typecheck (3→4), unit-shard-02 (5→7)
- Worker 4 (`5 → 7`): unit-shard-04 (5→7)

### Resource-class utilization

| Resource class | Capacity | Tasks | Reserved units | Peak concurrent usage | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| browser-lab | 1 | 1 | 2 | 1 | 12.5% | 14 | 0 | 0 |
| docker-builder | 1 | 2 | 3 | 1 | 18.8% | 13 | 0 | 0 |

### Worker-limited task table

| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| checkout | 1 | — | — | 0 | 0 | 1 | 0 | yes |
| install-deps | 1 | — | — | 1 | 1 | 3 | 0 | yes |
| build-app | 1 | — | — | 3 | 3 | 5 | 0 | yes |
| lint | 2 | — | — | 3 | 3 | 4 | 0 | no |
| typecheck | 3 | — | — | 3 | 3 | 4 | 0 | no |
| unit-shard-01 | 1 | — | — | 5 | 5 | 8 | 0 | yes |
| unit-shard-03 | 2 | — | — | 5 | 5 | 8 | 0 | yes |
| unit-shard-02 | 3 | — | — | 5 | 5 | 7 | 0 | no |
| unit-shard-04 | 4 | — | — | 5 | 5 | 7 | 0 | no |
| package-artifact | 1 | — | — | 8 | 8 | 9 | 0 | yes |
| build-container | 1 | docker-builder | docker-builder#1 | 9 | 9 | 11 | 0 | yes |
| publish-preview-image | 1 | docker-builder | docker-builder#1 | 11 | 11 | 12 | 0 | yes |
| security-scan | 2 | — | — | 11 | 11 | 13 | 0 | no |
| deploy-preview | 1 | — | — | 12 | 12 | 13 | 0 | yes |
| smoke-preview | 1 | browser-lab | browser-lab#1 | 13 | 13 | 15 | 0 | yes |
| promote-mainline | 1 | — | — | 15 | 15 | 16 | 0 | yes |

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| checkout | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | git checkout <git-sha> |
| install-deps | 1 | checkout | 2 | — | 1 | 3 | 1 | 3 | 0 | yes | pnpm install --frozen-lockfile |
| build-app | 2 | install-deps | 2 | — | 3 | 5 | 3 | 5 | 0 | yes | pnpm build |
| lint | 2 | install-deps | 1 | — | 3 | 4 | 7 | 8 | 4 | no | pnpm lint |
| typecheck | 2 | install-deps | 1 | — | 3 | 4 | 7 | 8 | 4 | no | pnpm typecheck |
| unit-shard-01 | 3 | build-app | 3 | — | 5 | 8 | 5 | 8 | 0 | yes | pnpm test:unit -- --shard=1/4 |
| unit-shard-02 | 3 | build-app | 2 | — | 5 | 7 | 6 | 8 | 1 | no | pnpm test:unit -- --shard=2/4 |
| unit-shard-03 | 3 | build-app | 3 | — | 5 | 8 | 5 | 8 | 0 | yes | pnpm test:unit -- --shard=3/4 |
| unit-shard-04 | 3 | build-app | 2 | — | 5 | 7 | 6 | 8 | 1 | no | pnpm test:unit -- --shard=4/4 |
| package-artifact | 4 | lint, typecheck, build-app, unit-shard-01, unit-shard-02, unit-shard-03, unit-shard-04 | 1 | — | 8 | 9 | 8 | 9 | 0 | yes | tar -czf dist/app.tgz dist/ |
| build-container | 5 | package-artifact | 2 | docker-builder | 9 | 11 | 9 | 11 | 0 | yes | docker build -t example/app:<git-sha> . |
| publish-preview-image | 6 | build-container | 1 | docker-builder | 11 | 12 | 11 | 12 | 0 | yes | docker push registry.example/app:<git-sha> |
| deploy-preview | 7 | publish-preview-image | 1 | — | 12 | 13 | 12 | 13 | 0 | yes | kubectl apply -f deploy/preview.yaml |
| security-scan | 6 | build-container | 2 | — | 11 | 13 | 13 | 15 | 2 | no | trivy image registry.example/app:<git-sha> |
| smoke-preview | 8 | deploy-preview | 2 | browser-lab | 13 | 15 | 13 | 15 | 0 | yes | pnpm exec playwright test --config preview |
| promote-mainline | 9 | smoke-preview, security-scan | 1 | — | 15 | 16 | 15 | 16 | 0 | yes | gh pr merge --auto --squash |

## Deterministic execution order

1. `checkout`
   - Dependencies: `ready at start`
   - Window: `0 → 1`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `git checkout <git-sha>`
2. `install-deps`
   - Dependencies: `checkout`
   - Window: `1 → 3`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `pnpm install --frozen-lockfile`
3. `build-app`
   - Dependencies: `install-deps`
   - Window: `3 → 5`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `pnpm build`
4. `lint`
   - Dependencies: `install-deps`
   - Window: `3 → 4`
   - Slack: `4`
   - Resources: `generic worker`
   - Command: `pnpm lint`
5. `typecheck`
   - Dependencies: `install-deps`
   - Window: `3 → 4`
   - Slack: `4`
   - Resources: `generic worker`
   - Command: `pnpm typecheck`
6. `unit-shard-01`
   - Dependencies: `build-app`
   - Window: `5 → 8`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `pnpm test:unit -- --shard=1/4`
7. `unit-shard-02`
   - Dependencies: `build-app`
   - Window: `5 → 7`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `pnpm test:unit -- --shard=2/4`
8. `unit-shard-03`
   - Dependencies: `build-app`
   - Window: `5 → 8`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `pnpm test:unit -- --shard=3/4`
9. `unit-shard-04`
   - Dependencies: `build-app`
   - Window: `5 → 7`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `pnpm test:unit -- --shard=4/4`
10. `package-artifact`
   - Dependencies: `lint`, `typecheck`, `build-app`, `unit-shard-01`, `unit-shard-02`, `unit-shard-03`, `unit-shard-04`
   - Window: `8 → 9`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `tar -czf dist/app.tgz dist/`
11. `build-container`
   - Dependencies: `package-artifact`
   - Window: `9 → 11`
   - Slack: `0`
   - Resources: `docker-builder`
   - Command: `docker build -t example/app:<git-sha> .`
12. `publish-preview-image`
   - Dependencies: `build-container`
   - Window: `11 → 12`
   - Slack: `0`
   - Resources: `docker-builder`
   - Command: `docker push registry.example/app:<git-sha>`
13. `deploy-preview`
   - Dependencies: `publish-preview-image`
   - Window: `12 → 13`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `kubectl apply -f deploy/preview.yaml`
14. `security-scan`
   - Dependencies: `build-container`
   - Window: `11 → 13`
   - Slack: `2`
   - Resources: `generic worker`
   - Command: `trivy image registry.example/app:<git-sha>`
15. `smoke-preview`
   - Dependencies: `deploy-preview`
   - Window: `13 → 15`
   - Slack: `0`
   - Resources: `browser-lab`
   - Command: `pnpm exec playwright test --config preview`
16. `promote-mainline`
   - Dependencies: `smoke-preview`, `security-scan`
   - Window: `15 → 16`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `gh pr merge --auto --squash`
