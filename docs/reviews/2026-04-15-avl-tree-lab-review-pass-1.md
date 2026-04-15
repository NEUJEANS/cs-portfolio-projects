# Review pass 1 - avl-tree-lab

## Focus
- initial test execution and import/runtime correctness

## Findings
1. `python3 -m unittest projects/avl-tree-lab/test_avl_tree_lab.py` failed because the test file imported `avl_tree_lab` without adding the project directory to `sys.path`.

## Fixes applied
- inserted `PROJECT_DIR` into `sys.path` before importing the module so the repo-local test command works from the repository root

## Verification
- reran the unittest command successfully after the import-path fix
