# 2026-04-15 distributed snapshot failure/recovery slice research

## Why this slice
The lab already covers markers, in-flight messages, Mermaid export, and concurrent snapshot IDs. The biggest remaining systems gap is showing how the snapshot tooling behaves when nodes temporarily fail and later recover.

## Scope choice
Keep the model lightweight and interview-friendly instead of simulating a full failure detector or retransmission protocol.

Chosen scope:
- model per-process up/down state
- reject sends from failed processes
- block deliveries into failed receivers until recovery
- let snapshots record process liveness alongside balances
- add a script runner so one CLI command can replay fail/recover/send/deliver/snapshot steps

## Why this is still portfolio-appropriate
- demonstrates state-machine thinking instead of only static algorithm output
- adds operational scenarios students can explain in interviews
- keeps the code small enough to test end to end
- makes Mermaid/JSON demos more realistic without pretending to be a production network simulator

## Deliberate non-goals for this run
- no automatic time-based recovery or retries
- no partition matrix or asymmetric link failures yet
- no message loss model; queued transfers remain queued until delivered or reported
