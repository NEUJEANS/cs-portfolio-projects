# Count-Min Sketch memory benchmark slice

## Goal
Add a concrete benchmark that compares Count-Min Sketch storage against an exact frequency table so the project demonstrates not just approximate counting, but also the space trade-off that motivates it.

## Notes
- A Count-Min Sketch is most compelling when the key space is large enough that exact per-item counts are expensive.
- For a portfolio-friendly benchmark, compare the Python object footprint of:
  - the sketch core tables only
  - the full demo-friendly sketch object including tracked observed items
  - an exact `collections.Counter`
- Reporting both `sketch_core_bytes` and `sketch_full_bytes` avoids misleading results, because the lab intentionally keeps observed items to support heavy-hitter demos and exact-count comparisons.

## Expected output
- stream size and unique-item count
- sketch width/depth derived from `epsilon` and `delta`
- exact counter bytes vs sketch bytes
- top-item sample showing exact counts, estimates, and overestimation

## Why this is a good slice
It adds interview-friendly evidence for the time/space trade-off claim already made in the README without forcing a rewrite of the current CLI architecture.
