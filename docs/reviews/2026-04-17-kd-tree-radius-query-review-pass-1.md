# KD-tree radius-query review - pass 1

## Focus
Diff audit of the new radius-query implementation, CLI wiring, tests, and README usage examples.

## Checks run
- Reviewed `radius_query(...)`, `brute_force_radius(...)`, and the new `radius` CLI block in `projects/kd-tree-spatial-search-lab/kd_tree_spatial_search.py`.
- Reviewed the new test coverage in `projects/kd-tree-spatial-search-lab/test_kd_tree_spatial_search.py`.
- Reviewed the README usage examples for command robustness.

## Findings
- The feature wiring and pruning logic looked correct.
- The README test command used bare `pytest`, which is less reproducible on machines where the console entry point is not installed globally.

## Fix applied
- Changed the README test command to `python3 -m pytest -q test_kd_tree_spatial_search.py`.

## Result
- The project docs now match the more portable invocation style used elsewhere in this repo.
