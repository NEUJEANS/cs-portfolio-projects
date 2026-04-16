# Distributed Snapshot Lab Research Note — 2026-04-16

## Goal
Add a meaningful next slice to the distributed snapshot project by separating directed link failures from whole-process crashes.

## Brief research summary
- Chandy-Lamport depends on per-channel marker propagation, so a useful extension is to make channel availability explicit instead of only toggling process liveness.
- For a student portfolio project, modeling directed link failures is a strong midpoint: it shows systems thinking without turning the simulator into a full network stack.
- The most interview-useful behavior is distinguishing **process down** from **link down** and showing how blocked markers and queued messages affect the observed global state.

## Scope chosen for this slice
- add directed link fail/recover operations
- block sends and deliveries on down links
- surface link state in snapshot JSON and Mermaid output
- support scripted `link-fail` / `link-recover` operations so scenarios stay resumable

## Deferred
- asymmetric message loss or retries
- partition groups / topology-wide fault injection
- richer step-by-step visualization assets generated automatically
