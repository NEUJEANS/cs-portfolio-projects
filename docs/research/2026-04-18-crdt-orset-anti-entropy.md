# crdt-orset-lab research — 2026-04-18 — anti-entropy slice

## Goal
Add a portfolio-friendly digest/delta report that explains how much OR-Set state needs to move during sync instead of treating replica reconciliation as a black box.

## Scope decision
Only a light terminology refresh was needed for this slice.

Core ideas kept in scope:
- **state-based OR-Set sync** can be described as shipping the whole replica state and merging it
- **delta-state / anti-entropy framing** is useful for teaching because students can compare the full-state payload with the subset of tags, tombstones, and counters the target is missing
- **digests** help summarize whether two replicas already match before sync without dumping the entire state into the narrative

## Implementation direction
1. capture a per-sync anti-entropy analysis directly on OR-Set `sync` timeline events
2. derive digest summaries and directional delta payloads from the same snapshot data used by the existing timeline renderers
3. export the analysis as Markdown / HTML / JSON so the merge-cost story is reviewable and screenshot-friendly
4. link those artifacts from the existing timeline/comparison pages instead of creating a separate disconnected workflow

## Deferred
- probabilistic or Merkle-tree-style reconciliation shortcuts
- real network transport benchmarking
- delta-CRDT mutation logs beyond the current state-diff teaching view
