# Learning refresh — 2026-04-18 — page replacement aging

## Quick refresher
- **Aging** approximates LRU by storing a short history of recent references instead of exact last-use timestamps.
- Each resident page keeps a **reference bit** and an **age counter**.
- On each aging tick, the counter shifts right and the current reference bit is inserted at the top bit.
- The page with the **smallest counter** is the coldest eviction candidate.

## Self-check
Reference string: `1 2 3 4 1 2 5 1 2 3 4 5`

Expected behavior in this simulator:
- Aging with 3 frames: `10` faults
- Aging with 4 frames: `8` faults
- Aging should stay close to LRU on the classic Belady workload because its short reference history still captures the main recency signal.

## Why this slice matters
- Clock shows a one-bit recency approximation.
- Aging shows a **multi-interval recency history**, which is a stronger systems story for interviews and portfolio walkthroughs.
- Together with FIFO / LRU / OPT, the lab now demonstrates a useful gradient from simple queueing to richer online heuristics to the offline optimum.
