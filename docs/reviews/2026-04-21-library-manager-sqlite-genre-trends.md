# library-manager-sqlite genre trend review log

Date: 2026-04-21

## Review pass 1, artifact wording and metadata surface
- Inspected the CLI surface and committed artifact bundle after the first implementation pass.
- Found issue: the new subject metadata existed in storage, but the plain catalog output did not surface it clearly enough for a quick CLI demo.
- Fix: added `--genre` on `add`, preserved genre values in catalog rows, and updated `format_book()` to show `genre:` inline.

## Review pass 2, SVG description accuracy
- Re-read the generated genre SVG and compared the descriptive text with the actual sample data.
- Found issue: the outer SVG description reported the requested top-limit count even when fewer genres actually touched the selected range.
- Fix: switched the outer genre SVG description to report the actual selected genre count instead of the raw requested limit.

## Review pass 3, determinism and smoke coverage
- Rebuilt the committed genre CSV and SVG artifacts from a seeded sample database using fixed dates and a fixed `--generated-at` timestamp.
- Re-ran the real `genre-trends` CLI twice and verified both CSV and SVG exports were byte-identical across runs and matched the committed artifacts.
- Confirmed a plain `list` CLI smoke now shows inline genre metadata for recruiter-friendly command-line demos.
- No further fixes were needed after the determinism pass.
