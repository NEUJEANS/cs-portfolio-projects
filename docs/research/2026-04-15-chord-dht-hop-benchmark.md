# Chord DHT hop benchmark research — 2026-04-15

## Goal
Add a portfolio-friendly benchmark slice to `chord-dht-lab` that makes the benefit of finger-table routing measurable instead of only descriptive.

## Notes
- Chord's main interview claim is logarithmic lookup behavior from finger-table jumps, so the project should expose that advantage directly.
- A good baseline is naive clockwise successor forwarding because it uses the same ring ownership rules but removes the finger-table shortcut.
- Keeping both strategies on the same ring and key set makes the comparison fair and easy to explain in a README or demo.
- Per-case route traces still matter: averages are useful, but students should also be able to inspect exactly which hops were skipped.

## Implementation direction
- add a `linear_lookup` path that always forwards to the immediate successor until the owner is reached
- add a `benchmark` CLI command that evaluates multiple keys across one or more chosen start nodes
- report both detailed cases and summary stats such as average hops, max hops, ties, and total hop savings
- keep the benchmark deterministic by reusing the existing JSON ring fixture and explicit key arguments

## Why this slice is strong
- it upgrades the project from static simulation to evidence-backed analysis
- it stays small enough for a single resumable run
- it creates better portfolio talking points: algorithmic complexity, baseline design, and empirical comparison
