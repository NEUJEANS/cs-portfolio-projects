# Chord DHT stabilization comparison slice

Date: 2026-04-15
Project: `chord-dht-lab`

## Why this slice
The lab could already simulate stabilization under one selected finger-repair policy, but it still made it awkward to explain *why* different `fix_fingers` schedules matter. For portfolio/demo use, a side-by-side comparison is more valuable than asking readers to mentally diff multiple separate CLI runs.

## Short research summary
- Chord maintenance is often discussed in terms of background tasks like `stabilize` and `fix_fingers`, but practical explanations usually compare convergence speed under different repair schedules.
- For an educational simulator, it is enough to run the same join/failure scenario under multiple deterministic policies and compare rounds-to-convergence plus partial progress when the round budget is limited.
- Seeded randomness is important here because students should be able to reproduce the same random `fix_fingers` order in screenshots, tests, and README examples.

## Implementation choice
Add a comparison helper and CLI command that:
1. runs the same stabilization scenario for `single`, `all`, and optional seeded `random` modes
2. records each full report for drill-down
3. emits a compact scoreboard with stabilization round and final finger-match progress
4. highlights the fastest fully-stabilized mode and the mode with the most progress under the chosen round budget
