# Review pass 3 - splay-tree trace + DOT

## Focus
Test coverage and regressions discovered while running automated checks.

## Findings
- Initial DOT assertion expected the wrong edge direction because the current root after inserts is 18, not 10.
- Repo-wide `pytest` collection is still blocked by broader project import-path layout issues outside this slice.

## Fixes applied
- Corrected the DOT structure assertion to match the actual tree.
- Verified the slice with `python3 -m unittest projects/splay-tree-lab/test_splay_tree_lab.py`.
- Recorded the broader pytest collection blocker for future repo hygiene work.
