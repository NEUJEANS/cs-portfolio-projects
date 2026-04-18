# Learning refresh — 2026-04-18 — page replacement lab

## Quick rules refresher
- **FIFO** evicts the page that has been resident the longest.
- **LRU** evicts the page whose most recent use is oldest.
- **OPT** evicts the page whose next use is farthest in the future (or never reused).
- **Belady's anomaly** can happen with FIFO because adding more frames does not guarantee a superset of resident pages.
- **LRU** and **OPT** are stack algorithms, so their page faults should not increase when frame counts increase.

## Self-test
Reference string: `1 2 3 4 1 2 5 1 2 3 4 5`

Expected page faults:
- FIFO with 3 frames: `9`
- FIFO with 4 frames: `10`
- LRU with 3 frames: `10`
- OPT with 3 frames: `7`

## Implementation note
For the first slice, a deterministic simulator with clear tie-breaking matters more than asymptotic optimization. OPT still uses future-position lookups so the replacement choice stays easy to explain in interviews and review logs.
