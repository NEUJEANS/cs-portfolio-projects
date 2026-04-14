# Vector Clock Lab Research

## Goal
Add a strong distributed-systems portfolio project that demonstrates causal ordering, conflict detection, and merge behavior without needing external infrastructure.

## Brief notes
- Vector clocks model causal history across replicas by keeping one logical counter per replica.
- For two versions A and B, A happens-before B when every clock entry in A is less than or equal to B and at least one entry is strictly less.
- If neither version dominates the other, the updates are concurrent and a conflict should be surfaced or merged.
- A good student portfolio slice is a replicated key-value store simulation with explicit version metadata, conflict detection, and deterministic merge tooling.

## Sources consulted
- https://en.wikipedia.org/wiki/Vector_clock
- https://www.geeksforgeeks.org/computer-networks/vector-clocks-in-distributed-systems/
- web search synthesis on educational replicated key-value store projects using vector clocks

## Scope chosen for this slice
- model vector clocks and comparison rules
- support replica-local writes that advance a replica clock
- simulate replication by importing remote versions
- detect conflicting versions for the same key
- provide a deterministic merge command that creates a causally newer resolved version
