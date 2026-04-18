# Review log — 2026-04-18 — page-replacement study artifacts

## Pass 1 — export/render audit
- Checked the new `study` artifact-export path end to end.
- Found two chart-quality issues:
  - the SVG y-axis rounded up to an awkward `13`
  - Clock overlapped FIFO exactly, making the second line hard to distinguish on the chart
- Fixes applied:
  - rounded the y-axis ceiling to a cleaner tick-aligned maximum
  - added distinct dash patterns so overlapping policies stay visually separable

## Pass 2 — README / artifact discoverability audit
- Re-read the project README after generating the committed artifact bundle.
- Found a docs gap: the README showed how to generate artifacts but did not point reviewers to the committed example outputs already shipped in the repo.
- Fix applied:
  - added a `Committed artifact examples` section linking the Markdown, SVG, and CSV study files

## Pass 3 — regression / smoke rerun
- Re-ran compile, unittest, and real CLI smoke coverage after the review fixes.
- Re-generated the committed artifact bundle and re-checked `git diff --check`.
- Result: no further issues found.

## Commands rerun in the final pass
- `python3 -m py_compile projects/page-replacement-lab/page_replacement_lab.py`
- `python3 -m unittest discover -s projects/page-replacement-lab -p 'test_*.py'`
- `python3 projects/page-replacement-lab/page_replacement_lab.py study --min-frames 2 --max-frames 6 --preset classic-belady --markdown-out docs/artifacts/page-replacement-lab/classic-belady-study.md --svg-out docs/artifacts/page-replacement-lab/classic-belady-study.svg --csv-out docs/artifacts/page-replacement-lab/classic-belady-study.csv`
- `python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 3 --preset classic-belady`
- `git diff --check`
