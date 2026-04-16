# HyperLogLog benchmark export assets research

## Goal
Add publishable benchmark assets for `hyperloglog-cardinality-lab` so the project can show results visually in a README or portfolio site without requiring a notebook or plotting stack.

## Decision
No new external web lookup was necessary for this slice.

Recent project research already established the two key facts this export layer needs:
- HyperLogLog error scales with the standard `1.04 / sqrt(m)` bound already exposed by the CLI.
- The benchmark rows already capture the portfolio-relevant tradeoff: precision/register count, dense memory proxy, and observed relative error.

That means this slice can focus on presentation and portability rather than algorithm changes.

## Asset strategy
- Keep the source of truth as the existing benchmark JSON rows.
- Add a CSV export so users can open the data in spreadsheets or notebooks.
- Add a self-contained SVG chart so the output works in GitHub, Markdown sites, and static hosting without extra Python plotting dependencies.
- Preserve deterministic output by reusing the existing seeded benchmark pipeline.

## Why SVG instead of a plotting dependency
- no extra install friction for students reviewing the repo
- easy to commit as a static artifact
- works well for README embeds and GitHub Pages
- keeps the project runnable in a minimal Python environment
