# Chord DHT lab research — 2026-04-15

## Goal
Add a compact but strong distributed-systems portfolio project beyond leader election and conflict repair.

## Notes reviewed
- Chord uses consistent hashing on an identifier ring and assigns each key to its successor node.
- Finger tables store shortcuts for identifiers `n + 2^i`, enabling expected logarithmic routing.
- A useful portfolio slice should make routing explainable, not just compute ownership silently.
- Join behavior is especially demo-friendly because it shows limited key movement after a node is added.

## Scope chosen for this slice
- simulate an `m`-bit identifier space with deterministic SHA-1 hashing (using 8 bits in the bundled demo to avoid tiny-ring collisions)
- generate finger tables for each node
- trace lookups from a starting node to the responsible owner
- preview key movement when a new node joins
- keep the implementation local and deterministic rather than modeling network transport or periodic stabilization

## Why this is portfolio-worthy
- connects distributed systems, hashing, routing, and asymptotic reasoning
- easy to demo live with JSON I/O and route traces
- leaves clear headroom for future slices like stabilization and churn handling
