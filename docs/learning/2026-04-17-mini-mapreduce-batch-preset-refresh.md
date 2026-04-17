# Mini MapReduce batch preset refresh

## Goal
Add one command path that can emit multiple annotation-view artifact variants without re-running the benchmark timings per view.

## Refresher notes
- Dataclass cloning can stay simple here: create a helper that reuses the existing benchmark metrics and swaps only `benchmark_notes`, `benchmark_note_annotations`, and `annotation_view`.
- Relative paths in a manifest should be computed from the batch output directory so committed artifacts remain portable across machines.
- If multiple views share the same benchmark execution, timing CSV and heatmap CSV should be written once and referenced by each preset rather than duplicated.

## Tiny self-test
- Base benchmark result should keep identical `timings_ms` / `heatmap_rows` across preset views.
- A `full` preset should preserve every structured annotation.
- A tighter preset can use severity filtering plus `annotation_limit=1` and `annotation_overflow='summary'` to produce a reviewer-friendly collapsed view.
