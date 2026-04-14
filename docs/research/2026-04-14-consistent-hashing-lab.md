# Consistent Hashing Lab Research — 2026-04-14

## Goal
Create a portfolio-friendly distributed-systems project that demonstrates consistent hashing rather than CRUD application work.

## Notes
- Consistent hashing places both nodes and keys on a ring so adding/removing nodes remaps only a fraction of keys.
- Virtual nodes improve distribution and reduce hotspots by spreading each physical node across multiple points on the ring.
- A useful student-sized slice is: reusable ring API, node add/remove, deterministic key assignment, distribution summary, and remap analysis for topology changes.

## Practical project decisions
- implement in Python for fast iteration and easy unit testing
- expose a CLI so the project is runnable without importing code
- support a simulation mode that shows how many keys move when a node is added or removed
- include a distribution report to make the systems behavior visible in portfolio screenshots

## References
- High Scalability: Consistent Hashing Algorithm
- Ably engineering blog: Implementing efficient consistent hashing
- ByteByteGo/system design primers on virtual nodes and minimal remapping
