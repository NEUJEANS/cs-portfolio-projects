# Flashcard quiz app review pass 2 — 2026-04-14

## Focus
History data integrity.

## Findings
1. History was initially keyed only by prompt, so two cards with the same prompt and different answers could overwrite each other.

## Fixes applied
- Switched persistent card identity to `prompt + tab + answer`.
- Preserved human-readable `prompt` and `answer` fields inside each record.
- Added a targeted test proving same-prompt/different-answer cards remain distinct.
