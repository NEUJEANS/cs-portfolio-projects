# network-flow-lab bipartite matching refresh

## Refresher
- In unweighted bipartite matching, every chosen pair consumes exactly one left node and one right node.
- A unit-capacity max-flow network models that constraint directly.
- After solving flow, any left->right edge carrying flow 1 is part of the matching.

## Self-check
- super-source to left capacity should be 1
- left-to-right compatibility edges should be 1
- right to super-sink capacity should be 1
- duplicate compatibility edges should not create duplicate matches in output

## Result
Confident enough to implement the matching helper on top of the existing Edmonds-Karp code and test both solver-level and CLI-level behavior.
