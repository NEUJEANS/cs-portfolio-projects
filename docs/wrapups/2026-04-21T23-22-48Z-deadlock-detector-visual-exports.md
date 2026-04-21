# Deadlock detector visual export slice — 2026-04-21T23:22:48Z

## What changed
- safely sync-checked `main` against `origin/main` before editing, then took the next deadlock-detector follow-up from the prior wrap-up: visual exports for the two deadlock-detection models
- extended `projects/deadlock-detector-lab/deadlock_detector.py` so `analyze-wait` and `analyze-allocations` now support `--svg-out` and `--html-out`
- added deterministic wait-for graph SVG/HTML reports with highlighted cycle edges, blocked-process emphasis, and an edge summary table
- added deterministic resource-allocation SVG/HTML reports with process/resource visuals, held-vs-request edge styling, shortage labels, and summary tables
- committed sample JSON, SVG, and HTML artifacts for both wait-for and allocation demos under `docs/artifacts/deadlock-detector-lab/`
- refreshed the project README plus checklist, research note, learning self-test, and review log so the slice is resumable

## Tests and validation run
- `python3 -m py_compile projects/deadlock-detector-lab/deadlock_detector.py projects/deadlock-detector-lab/test_deadlock_detector.py`
- `python3 -m unittest -v projects/deadlock-detector-lab/test_deadlock_detector.py` (`15/15`)
- `python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-wait projects/deadlock-detector-lab/sample_wait_graph.json --svg-out docs/artifacts/deadlock-detector-lab/sample_wait_graph.svg --html-out docs/artifacts/deadlock-detector-lab/sample_wait_graph.html`
- `python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-allocations projects/deadlock-detector-lab/sample_allocation_state.json --svg-out docs/artifacts/deadlock-detector-lab/sample_allocation_state.svg --html-out docs/artifacts/deadlock-detector-lab/sample_allocation_state.html`
- deterministic double-run `cmp` checks for wait-for JSON/SVG/HTML outputs
- deterministic double-run `cmp` checks for allocation JSON/SVG/HTML outputs
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git file:///home/user1_admin/.openclaw/workspace/cs-portfolio-projects --results=verified,unknown --fail`

## Reviews run
- pass 1: wait-for edge readability audit, fixed reverse-direction edge overlap by curving bidirectional waits so two-process cycles stay visible
- pass 2: allocation edge-label clarity audit, fixed opposing blocked-request label collisions and matched held-resource arrowheads to the blue held-edge styling
- pass 3: docs and artifact audit, fixed missing README/export guidance and committed deterministic sample visual artifacts plus resumability notes
- detailed review log: `docs/reviews/2026-04-21-deadlock-detector-visual-export-review.md`

## Feature commit
- `9a75a0fd04c7e415a86d3984fe05c0df0dd41d4b`

## Next step
- add a combined detection-vs-avoidance dashboard so the wait-for graph, allocation snapshot, and Banker's trace can be shown side-by-side in one portfolio report
