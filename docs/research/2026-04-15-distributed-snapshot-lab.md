# Distributed Snapshot Lab Research

## Goal
Add a new advanced distributed-systems project that feels stronger than another small CRUD/CLI exercise and gives a student a classic algorithm to explain in interviews.

## Notes
- Chandy-Lamport snapshots are a good fit because they are foundational, simulation-friendly, and self-contained.
- The most important concepts to surface are local state capture, marker propagation, recording in-transit messages on incoming channels, and a consistency invariant.
- A bank-transfer model keeps the scenario intuitive: balances are local state, queued transfers are channel state, and total money provides an easy correctness check.
- For a compact portfolio slice, it is enough to support one snapshot at a time with configurable marker arrival ordering.

## Scope for this slice
- build a CLI-driven simulator instead of a GUI
- include delayed-marker modeling so at least one test can prove that an in-flight message lands in the snapshot
- make JSON output readable enough for future visualization work
