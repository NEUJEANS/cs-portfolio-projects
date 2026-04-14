# Quadtree Spatial Index Lab Review - Pass 1

## Focus
Implementation correctness and basic demo usability.

## Issues found
1. The first draft tried to return nearest-neighbor state through a stale local variable, which could return `None` even after recursive updates.
2. The initial README told users to run `pytest`, but this environment does not provide pytest by default.

## Fixes applied
- rewired nearest-neighbor search to use a mutable best-reference container correctly
- updated README commands to use `python3`
- updated test instructions to use `python3 -m unittest`
