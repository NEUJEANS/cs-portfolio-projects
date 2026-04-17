# KD-tree radius-query review - pass 2

## Focus
CLI-output and artifact-readability review for the committed radius-query sample.

## Checks run
- Ran `python3 projects/kd-tree-spatial-search-lab/kd_tree_spatial_search.py projects/kd-tree-spatial-search-lab/sample_points.json radius 7 2 3 --limit 2` and inspected the JSON payload.
- Inspected `docs/artifacts/kd-tree-radius-query-sample.json` and the README artifact note side-by-side.

## Findings
- The committed artifact itself was correct.
- The README artifact note did not mention that the sample uses a radius of 3 and keeps the top 3 matches, which made the example less self-explanatory.

## Fix applied
- Clarified the README artifact note to describe the exact sample query shape (`radius=3`, centered at `(7, 2)`, top 3 matches).

## Result
- The sample artifact is easier to understand without opening the generator command history.
