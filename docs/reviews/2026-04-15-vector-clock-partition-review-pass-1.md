# Vector Clock Lab Review Pass 1

## Focus
Correctness of the new partition/heal simulation.

## Findings
1. Initial implementation used one shared store during the partition phase, so it did not really isolate visibility by partition.

## Fixes applied
- switched the partition workflow to isolated per-partition stores
- only union conflicting versions during heal/anti-entropy
- merged partition-local replica clocks back into the healed global store before replication

## Result
The scenario now models divergence-before-heal more faithfully.
