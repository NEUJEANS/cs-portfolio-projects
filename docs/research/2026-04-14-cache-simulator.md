# Cache Simulator Research — 2026-04-14

Goal: add a systems-oriented portfolio project that demonstrates memory hierarchy fundamentals, trace-driven simulation, and careful metrics.

Key notes from brief research:
- A strong educational slice should expose cache geometry clearly: total size, block size, associativity, and derived set count.
- Address decomposition (tag / set index / block offset) is core to the learning value.
- LRU is the most recognizable replacement policy for an introductory but still credible simulator.
- Supporting both reads and writes makes the simulator feel more realistic than read-only traces.
- Write-through and write-back are both worth surfacing because they change memory traffic and dirty-eviction behavior.

Planned vertical slice:
- Python CLI that simulates reads/writes from a JSON trace.
- Configurable total size, block size, associativity, replacement policy (LRU), and write policy (write-through or write-back).
- Human-readable summary plus JSON output.
- Tests covering address mapping, hit/miss accounting, LRU eviction, dirty write-back, and CLI flow.

References consulted:
- Educational cache simulator guides and course assignments surfaced by web search.
- Common architecture explanations of direct-mapped vs set-associative caches and write policies.
