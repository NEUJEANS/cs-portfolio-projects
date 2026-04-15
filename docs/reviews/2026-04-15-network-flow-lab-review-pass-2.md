# network-flow-lab review pass 2

## Focus
Input-validation and data-shape review.

## Findings
1. Matching partitions were required to be disjoint, but duplicate names inside a single partition were not rejected.
2. Duplicate node names would produce ambiguous or inflated internal source/sink edges.

## Fixes applied
- added duplicate-node validation for left/right partitions
- added regression tests for duplicate and reserved names
