# Flashcard quiz app review pass 3 — 2026-04-14

## Focus
Docs/test alignment and output clarity.

## Findings
1. README history JSON example needed to reflect the actual storage key format after the pass-2 fix.
2. Persistent summary output was more useful with an explicit aggregate accuracy value.

## Fixes applied
- Updated the README data-format section to show the composite history key and explain why it exists.
- Included percentage accuracy in the printed history summary.
- Re-ran the focused test suite after the doc/code tweaks.
