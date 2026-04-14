# Static Site Generator Review — Pass 2 (2026-04-14)

## Focus
Generated-site usability and portfolio presentation.

## Findings
1. Filename fallback titles were not presentation-friendly for pages without explicit front matter titles.
2. The project README undersold the project by describing it as a generic converter instead of a multi-page portfolio builder.

## Fixes applied
- added `humanizeTitle()` so filenames like `about_me.md` render as `About Me`
- updated the README to highlight metadata-driven multi-page generation and portfolio use cases

## Validation
- `npm test`
