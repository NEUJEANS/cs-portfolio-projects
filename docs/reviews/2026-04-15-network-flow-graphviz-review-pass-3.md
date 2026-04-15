# network-flow graphviz review pass 3

## Focus
Docs, smoke-test behavior, and resumability.

## Findings
1. README commands match the implemented CLI flags.
2. `python3 -m unittest tests/test_network_flow_lab.py` passes after the export-path fix.
3. Demo and match-demo smoke checks generate reusable DOT artifacts without requiring Graphviz to be installed.

## Fixes applied
- no additional code changes needed after this pass
