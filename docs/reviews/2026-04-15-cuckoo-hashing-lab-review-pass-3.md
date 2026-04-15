# 2026-04-15 Cuckoo hashing lab review pass 3

## Focus
Metrics integrity and documentation audit.

## Issue found
- Snapshot counters such as `rehash_count` and `displacement_count` were accepted even if negative, which could produce nonsense stats after manual edits or bad fixtures.

## Fix
- Added validation that snapshot counters must be non-negative.
- Extended invalid-snapshot coverage and updated the root README progress list so the new lab appears in the portfolio index.

## Result
- Stats output is now more trustworthy, and the repo-level docs reflect the new project.
