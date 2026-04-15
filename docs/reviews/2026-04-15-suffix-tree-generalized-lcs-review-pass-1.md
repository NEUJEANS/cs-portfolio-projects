# Review pass 1 — suffix-tree generalized LCS

## Focus
Correctness of generalized suffix tree construction and source-boundary handling.

## Findings
- Confirmed the new two-text path uses distinct sentinels so common substrings cannot span across text boundaries.
- Found a reproducibility issue risk: child traversal order in the generalized-tree DFS was relying on dictionary iteration, which could make equal-length LCS tie resolution less predictable across runs.

## Fixes applied
- Sorted child traversal by edge label.
- Added deterministic tie-breaking using position lists and candidate text so output stays stable.

## Verification
- `python -m pytest -q projects/suffix-tree-lab/test_suffix_tree_lab.py`
- `python -m py_compile projects/suffix-tree-lab/suffix_tree_lab.py`
