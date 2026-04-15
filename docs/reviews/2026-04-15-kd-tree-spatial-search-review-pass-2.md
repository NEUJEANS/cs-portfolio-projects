# Review Pass 2 — KD-Tree Spatial Search Lab

## Checks
- inspected nearest-neighbor branch ordering
- inspected tie behavior on equal distances
- checked invalid-input handling

## Issues found
1. Equal-distance nearest candidates needed a deterministic tie-break rule.
2. Invalid rectangle bounds should fail fast instead of silently returning no matches.

## Fixes applied
- added deterministic tuple-based tie-breaking in nearest-neighbor search
- raised `ValueError` for invalid rectangle bounds
