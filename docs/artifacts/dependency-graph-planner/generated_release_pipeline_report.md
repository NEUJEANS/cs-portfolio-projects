# Dependency graph walkthrough — Generated Release Pipeline

- Source manifest: `projects/dependency-graph-planner/generated_release_pipeline.json`
- Task count: `19`
- Parallel layers: `14`
- Estimated makespan: `21`
- Critical path: `freeze-release-branch -> build-macos -> sign-macos -> publish-candidates -> deploy-staging -> verify-staging -> canary-10pct -> verify-canary-01 -> canary-50pct -> verify-canary-02 -> canary-90pct -> verify-canary-03 -> full-rollout -> announce-release`
- Worker-limited makespan (3 workers): `24`
- Worker-limited strategy: `critical-first`

## Linked artifacts

- [GitHub-friendly Mermaid preview](generated_release_pipeline_mermaid.md)
- [Mermaid source](generated_release_pipeline.mmd)
- [Graphviz DOT source](generated_release_pipeline.dot)
- [Report dashboard HTML](generated_release_pipeline_report_dashboard.html)
- [Worker-limited schedule SVG](generated_release_pipeline_3_workers_schedule.svg)
- [Worker-limited schedule JSON](generated_release_pipeline_3_workers_schedule.json)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `freeze-release-branch, assemble-release-notes, build-linux, build-macos, build-windows, sign-linux, sign-macos, sign-windows, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release`
- widest parallel layer: `layer 1` with `4` task(s): `assemble-release-notes`, `build-linux`, `build-macos`, `build-windows`
- non-critical slack budget available for schedule tradeoffs: `8` time units
- worker-limited dispatch uses critical-first, low-slack, longer-duration tie-breaking across `3 workers`
- worker cap increases makespan by `3` time unit(s) over the unlimited-layer bound of `21`
- utilization under the worker cap: `41.7%` with `42` idle worker-time unit(s)
- biggest queue delay: `sign-windows` waited `4` time unit(s) after becoming ready on `signing#1`
- renewable resource caps active for the constrained run: `prod-slot=1, signing=1`
- compared worker caps against the unlimited baseline of `21`: `3 workers → 24`

## Parallel layer windows

- Layer 0 (`0` → `1`): `freeze-release-branch`
- Layer 1 (`1` → `4`): `assemble-release-notes`, `build-linux`, `build-macos`, `build-windows`
- Layer 2 (`3` → `6`): `sign-linux`, `sign-macos`, `sign-windows`
- Layer 3 (`6` → `7`): `publish-candidates`
- Layer 4 (`7` → `8`): `deploy-staging`
- Layer 5 (`8` → `10`): `verify-staging`
- Layer 6 (`10` → `11`): `canary-10pct`
- Layer 7 (`11` → `13`): `verify-canary-01`
- Layer 8 (`13` → `14`): `canary-50pct`
- Layer 9 (`14` → `16`): `verify-canary-02`
- Layer 10 (`16` → `17`): `canary-90pct`
- Layer 11 (`17` → `19`): `verify-canary-03`
- Layer 12 (`19` → `20`): `full-rollout`
- Layer 13 (`20` → `21`): `announce-release`

## Worker-capacity comparison

| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 workers | 24 | 3 | 21 | 41.7% | 42 | 3 | 4 |

## Worker-limited comparison

- Worker limit: `3`
- Strategy: `critical-first`
- Total work: `30`
- Theoretical lower bound: `21`
- Unlimited layered makespan: `21`
- Worker-limited makespan: `24`
- Dispatch order: `freeze-release-branch, build-macos, build-linux, build-windows, sign-linux, assemble-release-notes, sign-macos, sign-windows, publish-candidates, deploy-staging, verify-staging, canary-10pct, verify-canary-01, canary-50pct, verify-canary-02, canary-90pct, verify-canary-03, full-rollout, announce-release`

### Worker timelines

- Worker 1 (`0 → 24`): freeze-release-branch (0→1), build-macos (1→4), sign-macos (5→7) [signing#1], sign-windows (7→9) [signing#1], publish-candidates (9→10), deploy-staging (10→11), verify-staging (11→13), canary-10pct (13→14) [prod-slot#1], verify-canary-01 (14→16), canary-50pct (16→17) [prod-slot#1], verify-canary-02 (17→19), canary-90pct (19→20) [prod-slot#1], verify-canary-03 (20→22), full-rollout (22→23) [prod-slot#1], announce-release (23→24)
- Worker 2 (`1 → 5`): build-linux (1→3), sign-linux (3→5) [signing#1]
- Worker 3 (`1 → 4`): build-windows (1→3), assemble-release-notes (3→4)

### Resource-class utilization

| Resource class | Capacity | Tasks | Reserved units | Peak concurrent usage | Utilization | Idle capacity | Delayed tasks | Max queue delay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prod-slot | 1 | 4 | 4 | 1 | 16.7% | 20 | 0 | 0 |
| signing | 1 | 3 | 6 | 1 | 25.0% | 18 | 2 | 4 |

### Worker-limited task table

| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| freeze-release-branch | 1 | — | — | 0 | 0 | 1 | 0 | yes |
| build-macos | 1 | — | — | 1 | 1 | 4 | 0 | yes |
| build-linux | 2 | — | — | 1 | 1 | 3 | 0 | no |
| build-windows | 3 | — | — | 1 | 1 | 3 | 0 | no |
| sign-linux | 2 | signing | signing#1 | 3 | 3 | 5 | 0 | no |
| assemble-release-notes | 3 | — | — | 1 | 3 | 4 | 2 | no |
| sign-macos | 1 | signing | signing#1 | 4 | 5 | 7 | 1 | yes |
| sign-windows | 1 | signing | signing#1 | 3 | 7 | 9 | 4 | no |
| publish-candidates | 1 | — | — | 9 | 9 | 10 | 0 | yes |
| deploy-staging | 1 | — | — | 10 | 10 | 11 | 0 | yes |
| verify-staging | 1 | — | — | 11 | 11 | 13 | 0 | yes |
| canary-10pct | 1 | prod-slot | prod-slot#1 | 13 | 13 | 14 | 0 | yes |
| verify-canary-01 | 1 | — | — | 14 | 14 | 16 | 0 | yes |
| canary-50pct | 1 | prod-slot | prod-slot#1 | 16 | 16 | 17 | 0 | yes |
| verify-canary-02 | 1 | — | — | 17 | 17 | 19 | 0 | yes |
| canary-90pct | 1 | prod-slot | prod-slot#1 | 19 | 19 | 20 | 0 | yes |
| verify-canary-03 | 1 | — | — | 20 | 20 | 22 | 0 | yes |
| full-rollout | 1 | prod-slot | prod-slot#1 | 22 | 22 | 23 | 0 | yes |
| announce-release | 1 | — | — | 23 | 23 | 24 | 0 | yes |

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| freeze-release-branch | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | gh release create --draft vNEXT |
| assemble-release-notes | 1 | freeze-release-branch | 1 | — | 1 | 2 | 5 | 6 | 4 | no | gh release view --json body |
| build-linux | 1 | freeze-release-branch | 2 | — | 1 | 3 | 2 | 4 | 1 | no | python -m build --wheel |
| build-macos | 1 | freeze-release-branch | 3 | — | 1 | 4 | 1 | 4 | 0 | yes | python -m build --wheel --plat-name macosx_14_0_arm64 |
| build-windows | 1 | freeze-release-branch | 2 | — | 1 | 3 | 2 | 4 | 1 | no | python -m build --wheel --plat-name win_amd64 |
| sign-linux | 2 | build-linux | 2 | signing | 3 | 5 | 4 | 6 | 1 | no | cosign sign dist/linux/* |
| sign-macos | 2 | build-macos | 2 | signing | 4 | 6 | 4 | 6 | 0 | yes | cosign sign dist/macos/* |
| sign-windows | 2 | build-windows | 2 | signing | 3 | 5 | 4 | 6 | 1 | no | cosign sign dist/windows/* |
| publish-candidates | 3 | assemble-release-notes, sign-linux, sign-macos, sign-windows | 1 | — | 6 | 7 | 6 | 7 | 0 | yes | gh release upload vNEXT dist/* --clobber |
| deploy-staging | 4 | publish-candidates | 1 | — | 7 | 8 | 7 | 8 | 0 | yes | kubectl apply -f deploy/staging.yaml |
| verify-staging | 5 | deploy-staging | 2 | — | 8 | 10 | 8 | 10 | 0 | yes | pytest tests/smoke/test_release_candidate.py |
| canary-10pct | 6 | verify-staging | 1 | prod-slot | 10 | 11 | 10 | 11 | 0 | yes | gcloud deploy releases promote --percent=10 |
| verify-canary-01 | 7 | canary-10pct | 2 | — | 11 | 13 | 11 | 13 | 0 | yes | check error budget after 10% traffic |
| canary-50pct | 8 | verify-canary-01 | 1 | prod-slot | 13 | 14 | 13 | 14 | 0 | yes | gcloud deploy releases promote --percent=50 |
| verify-canary-02 | 9 | canary-50pct | 2 | — | 14 | 16 | 14 | 16 | 0 | yes | check error budget after 50% traffic |
| canary-90pct | 10 | verify-canary-02 | 1 | prod-slot | 16 | 17 | 16 | 17 | 0 | yes | gcloud deploy releases promote --percent=90 |
| verify-canary-03 | 11 | canary-90pct | 2 | — | 17 | 19 | 17 | 19 | 0 | yes | check error budget after 90% traffic |
| full-rollout | 12 | verify-canary-03 | 1 | prod-slot | 19 | 20 | 19 | 20 | 0 | yes | gcloud deploy releases promote --to-target=prod |
| announce-release | 13 | full-rollout | 1 | — | 20 | 21 | 20 | 21 | 0 | yes | gh release edit vNEXT --draft=false |

## Deterministic execution order

1. `freeze-release-branch`
   - Dependencies: `ready at start`
   - Window: `0 → 1`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `gh release create --draft vNEXT`
2. `assemble-release-notes`
   - Dependencies: `freeze-release-branch`
   - Window: `1 → 2`
   - Slack: `4`
   - Resources: `generic worker`
   - Command: `gh release view --json body`
3. `build-linux`
   - Dependencies: `freeze-release-branch`
   - Window: `1 → 3`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `python -m build --wheel`
4. `build-macos`
   - Dependencies: `freeze-release-branch`
   - Window: `1 → 4`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python -m build --wheel --plat-name macosx_14_0_arm64`
5. `build-windows`
   - Dependencies: `freeze-release-branch`
   - Window: `1 → 3`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `python -m build --wheel --plat-name win_amd64`
6. `sign-linux`
   - Dependencies: `build-linux`
   - Window: `3 → 5`
   - Slack: `1`
   - Resources: `signing`
   - Command: `cosign sign dist/linux/*`
7. `sign-macos`
   - Dependencies: `build-macos`
   - Window: `4 → 6`
   - Slack: `0`
   - Resources: `signing`
   - Command: `cosign sign dist/macos/*`
8. `sign-windows`
   - Dependencies: `build-windows`
   - Window: `3 → 5`
   - Slack: `1`
   - Resources: `signing`
   - Command: `cosign sign dist/windows/*`
9. `publish-candidates`
   - Dependencies: `assemble-release-notes`, `sign-linux`, `sign-macos`, `sign-windows`
   - Window: `6 → 7`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `gh release upload vNEXT dist/* --clobber`
10. `deploy-staging`
   - Dependencies: `publish-candidates`
   - Window: `7 → 8`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `kubectl apply -f deploy/staging.yaml`
11. `verify-staging`
   - Dependencies: `deploy-staging`
   - Window: `8 → 10`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `pytest tests/smoke/test_release_candidate.py`
12. `canary-10pct`
   - Dependencies: `verify-staging`
   - Window: `10 → 11`
   - Slack: `0`
   - Resources: `prod-slot`
   - Command: `gcloud deploy releases promote --percent=10`
13. `verify-canary-01`
   - Dependencies: `canary-10pct`
   - Window: `11 → 13`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `check error budget after 10% traffic`
14. `canary-50pct`
   - Dependencies: `verify-canary-01`
   - Window: `13 → 14`
   - Slack: `0`
   - Resources: `prod-slot`
   - Command: `gcloud deploy releases promote --percent=50`
15. `verify-canary-02`
   - Dependencies: `canary-50pct`
   - Window: `14 → 16`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `check error budget after 50% traffic`
16. `canary-90pct`
   - Dependencies: `verify-canary-02`
   - Window: `16 → 17`
   - Slack: `0`
   - Resources: `prod-slot`
   - Command: `gcloud deploy releases promote --percent=90`
17. `verify-canary-03`
   - Dependencies: `canary-90pct`
   - Window: `17 → 19`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `check error budget after 90% traffic`
18. `full-rollout`
   - Dependencies: `verify-canary-03`
   - Window: `19 → 20`
   - Slack: `0`
   - Resources: `prod-slot`
   - Command: `gcloud deploy releases promote --to-target=prod`
19. `announce-release`
   - Dependencies: `full-rollout`
   - Window: `20 → 21`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `gh release edit vNEXT --draft=false`
