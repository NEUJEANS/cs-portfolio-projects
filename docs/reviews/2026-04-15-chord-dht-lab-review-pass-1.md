# Chord DHT lab review — pass 1

## Focus
Core correctness of identifier mapping, finger tables, and lookup routing.

## Issue found
- The initial bundled 5-bit demo ring produced a hash collision between `alpha` and `echo`, which made the sample topology invalid and broke tests.

## Fix applied
- Increased the bundled demo/ring fixture to 8 bits so the default project examples stay collision-free while still remaining easy to inspect.
- Updated related docs and fixtures to match the larger ring.

## Result
- The demo topology now builds deterministically and the core tests can exercise the intended routing behavior.
