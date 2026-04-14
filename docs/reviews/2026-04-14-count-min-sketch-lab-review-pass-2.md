# Review pass 2 — count-min-sketch-lab

## Focus
Benchmark interpretation and portfolio honesty.

## Issue found
- The benchmark can show that an exact `Counter` beats the sketch on tiny streams with very few unique keys, which could confuse readers if not explained.

## Fix applied
- Updated the README architecture notes to clarify that the benchmark is intentionally honest: small Python workloads may favor exact counting, while CMS is more compelling as the key space or memory pressure grows.

## Validation
- Ran `benchmark-memory` on the sample stream and confirmed the output now matches the documented caveat.
