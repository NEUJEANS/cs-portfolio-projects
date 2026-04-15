# Review pass 1 — suffix-tree suffix-array benchmark slice

## Focus
Execution sanity after adding the suffix-array baseline.

## Checks
- ran `./.venv/bin/pytest -q projects/suffix-tree-lab/test_suffix_tree_lab.py`
- failure found: suffix-array lookup returned match offsets in lexicographic suffix order instead of ascending text order

## Fix applied
- sorted suffix-array match offsets before returning so benchmark baselines line up with the tree implementation and CLI expectations

## Result
- rerun passed after the fix
