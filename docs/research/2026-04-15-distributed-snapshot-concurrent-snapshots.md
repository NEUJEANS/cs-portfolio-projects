# Concurrent snapshots research notes

## Goal
Add a follow-up slice to the distributed snapshot lab that demonstrates how multiple snapshots can coexist without mixing channel state.

## Key ideas
- Chandy-Lamport markers need a snapshot identifier when more than one snapshot may be active at the same time.
- Each process should keep per-snapshot recording state so markers for snapshot `blue` do not close channels for snapshot `green`.
- For a compact portfolio lab, a good teaching slice is a named multi-snapshot runner that reuses the same transfer timeline and reports isolated results per snapshot.

## Practical scope for this repo
- keep the existing single-snapshot CLI unchanged for backward compatibility
- add a `concurrent` mode with explicit `snapshot_id:initiator` inputs
- support per-snapshot marker delays so each named snapshot can record different in-flight channels
- return a JSON bundle keyed by snapshot id

## Self-check
- If snapshot `blue` starts at `A` and `green` starts at `C`, can the same in-flight execution produce different recorded channel states? Yes, if marker arrival ordering differs per snapshot.
- What is the easiest bug to avoid? Accidentally sharing closed-channel state across snapshot IDs.
