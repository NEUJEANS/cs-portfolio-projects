# Learning refresh — 2026-04-18 — page-replacement clock + presets slice

## Quick rules refresher
- **Clock / second-chance** keeps pages in a circular frame list with a moving hand.
- On a hit, the page's reference bit becomes `1`.
- On a miss with full memory, Clock scans from the current hand position, clears `1` bits to `0`, and evicts the first page it finds with a `0` bit.
- If every page has reference bit `1`, Clock effectively makes a full cleanup pass before choosing a victim.
- **LRU** and **OPT** are stack algorithms, so page faults should not increase as frame count increases.
- **FIFO** is not a stack algorithm, and Clock can still regress on some workloads even though it often approximates recency better than FIFO.

## Self-test
Reference string: `1 2 3 4 1 2 5 1 2 3 4 5`

Expected page faults with 3 frames:
- FIFO: `9`
- Clock: `9`
- LRU: `10`
- OPT: `7`

Expected regressions in a `2..5` frame study:
- FIFO increases from `9` to `10` faults when moving from `3` to `4` frames
- Clock also increases from `9` to `10` faults on that same workload
- LRU and OPT stay monotonic on this workload

## Implementation note
Use deterministic slot order and hand movement so the step traces stay stable across tests, docs, and future chart exports.
