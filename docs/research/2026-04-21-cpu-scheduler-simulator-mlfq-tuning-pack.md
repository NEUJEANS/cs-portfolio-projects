# CPU Scheduler Simulator Research — 2026-04-21 MLFQ Tuning Pack Slice

## Why this slice
The scheduler project already covered MLFQ itself, but the benchmark story still treated it as one fixed policy. The next weak spot was explaining how different queue ladders change the tradeoff between response time, fairness, and dispatch overhead.

## External research decision
- skipped new external web research for this run because the slice extends the repo's existing MLFQ implementation, compare flow, and benchmark artifact pipeline directly
- reused the repo's prior MLFQ understanding and focused this run on packaging policy-tuning evidence into reproducible benchmark outputs

## Modeling choices for this repo
- keep run-mode MLFQ unchanged so single-policy experiments stay simple and backwards compatible
- add named `--mlfq-variant-pack` expansion only in compare and benchmark mode, where side-by-side tuning evidence actually matters
- ship one initial `portfolio` pack with three clearly different ladders:
  - `interactive`: `1,2,4` with boost `8`
  - `balanced`: `2,4,8` with boost `12`
  - `throughput`: `4,8,16` with boosts off
- commit a focused artifact bundle under `docs/artifacts/cpu-scheduler-simulator/mlfq-tuning-pack/` so the tuning story is demo-ready without custom setup

## Expected portfolio value
- makes the project look more like a scheduler case study than a one-algorithm toy
- gives recruiters a concrete example of policy tuning, not just algorithm selection
- keeps every tuning claim grounded in deterministic benchmark artifacts and tests
