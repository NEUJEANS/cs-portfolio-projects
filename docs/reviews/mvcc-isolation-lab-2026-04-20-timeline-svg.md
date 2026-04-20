# MVCC isolation lab review — 2026-04-20 — timeline SVG slice

## Pass 1 — SVG accessibility wiring
- Re-read the generated SVG as raw markup instead of only looking at the rendered picture.
- Issue found: the root `<svg>` used `aria-labelledby="title desc"`, but the generated `<title>` and `<desc>` elements did not carry matching ids.
- Fix: switched the export to `aria-labelledby="timeline-title timeline-desc"` and emitted matching `id` attributes on both metadata elements, then added regression coverage for those strings.

## Pass 2 — rounded-corner renderer compatibility
- Re-read the SVG from a portability/standards perspective, especially the rectangle styling.
- Issue found: rounded corners were declared through CSS `rx`/`ry` on shared classes, which is not a reliable cross-renderer approach for SVG rectangles.
- Fix: moved rounded corners onto the concrete `<rect>` attributes for event/version cards and removed the dead CSS declarations.

## Pass 3 — JSON export regression coverage
- Re-read the CLI surface from the perspective of downstream scripts that may request both JSON and timeline outputs.
- Issue found: the slice exposed `_meta` paths for timeline exports, but the test suite did not prove those fields stay present in JSON mode for either `run` or `compare`.
- Fix: added regression tests for `run --json --timeline-svg-out ...` and `compare --json --timeline-svg-dir ...` so future refactors cannot silently drop the export metadata.

## Final verification
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/doctor_on_call.json --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/repeatable_read_window.json --markdown-out docs/artifacts/mvcc-isolation-lab/repeatable_read_window_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- deterministic double-export hash check for the three `doctor_on_call_*_timeline.svg` files
- `git diff --check`
