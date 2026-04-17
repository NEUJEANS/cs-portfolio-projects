# KD-tree radius-query mode

- Timestamp: `2026-04-17 15:30 UTC`
- Feature commit: `fd2bc13cb416dcd916f4f73b7427fe0b8d7fabac`

## What changed
- Added `KDTree.radius_query(...)` with branch pruning, non-negative radius validation, and optional result limits.
- Added a `radius` CLI command that returns distance-annotated JSON matches sorted by Euclidean distance.
- Added `brute_force_radius(...)` so tests can compare KD-tree radius results against a simple reference implementation.
- Extended the KD-tree test suite with radius-query correctness, limit-handling, validation, and CLI-output coverage.
- Updated the KD-tree README plus project checklist to advertise the new circular-query capability.
- Added a committed sample artifact at `docs/artifacts/kd-tree-radius-query-sample.json`.
- Logged three review passes for diff quality, artifact clarity, and final publish-safety.

## Tests and scans run
- `./.venv/bin/python -m py_compile projects/kd-tree-spatial-search-lab/kd_tree_spatial_search.py`
- `./.venv/bin/python -m pytest -q projects/kd-tree-spatial-search-lab/test_kd_tree_spatial_search.py`
- `python3 projects/kd-tree-spatial-search-lab/kd_tree_spatial_search.py projects/kd-tree-spatial-search-lab/sample_points.json radius 7 2 3 --limit 3 > /tmp/kd-tree-radius-query-sample.json`
- `diff -u /tmp/kd-tree-radius-query-sample.json docs/artifacts/kd-tree-radius-query-sample.json`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Review passes
1. Diff audit of the radius-query implementation, tests, and README; fixed the README to use `python3 -m pytest` instead of bare `pytest`.
2. CLI/artifact-readability review; clarified that the committed sample artifact uses a radius of 3 and keeps the top 3 matches.
3. Final correctness + publish-safety review; re-ran compile/tests, regenerated the sample artifact, and confirmed the generated JSON matched the committed artifact.

## Next step
- Add an optional visualization/export mode that plots the query circle and highlighted matches so the KD-tree project has a slide-ready geometry artifact in addition to raw JSON.
