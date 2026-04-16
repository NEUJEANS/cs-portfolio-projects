# Review Pass 1 — markdown-notes-search section results

Date: 2026-04-16
Focus: code-path review after the first implementation pass

## Checks
- Read the section-results expansion path in `projects/markdown-notes-search/notes_search.py`
- Re-ran the unit suite after the refactor

## Findings
1. Boolean-query handling was effectively evaluating the postfix matcher twice for notes that had no positive terms, which was unnecessary and made the section-results path harder to reason about.

## Fixes applied
- Changed `build_matching_terms()` to return both `matched` status and `matched_terms`
- Simplified `search_notes()` so it skips unmatched notes without a second postfix evaluation

## Verification
- `python3 -m unittest discover -s projects/markdown-notes-search -p 'test_*.py'`
