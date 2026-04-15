# Review pass 2 - splay-tree trace + DOT

## Focus
Visualization output quality and CLI usability.

## Findings
- DOT export needed explicit root emphasis and optional highlighted keys to make screenshots/rendered graphs portfolio-friendly.
- The feature needed a single command that can emit before/after artifacts without extra scripting.

## Fixes applied
- Root nodes now render with a thicker border.
- Highlighted access keys render with a filled style.
- Added `trace` CLI support with `--before-dot` and `--after-dot` outputs.
