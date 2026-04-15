# Review pass 3 - avl-tree-lab

## Focus
- docs/repo integration and output sanity

## Findings
1. The root repository README did not yet list the new project, which would make the slice easy to miss.
2. The project needed a final smoke check that CLI demo output stays valid JSON after the error-handling changes.

## Fixes applied
- added `avl-tree-lab` to the repository-level project list
- ran `python3 projects/avl-tree-lab/avl_tree_lab.py demo --trace | python3 -m json.tool` as a JSON-output smoke check

## Verification
- README now includes the project
- demo command output parses cleanly as JSON
