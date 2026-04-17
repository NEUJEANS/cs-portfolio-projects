# Markdown Notes Search grouped TUI clusters

- Timestamp: `2026-04-17 15:55 UTC`
- Feature commit: `08d75d2a0154583023ae21299c25163036b32609`

## What changed
- Added grouped TUI rows so dense `--section-results` clusters from the same note can collapse into one note-level entry.
- Kept mark/open/export flows reversible by expanding grouped rows back into their underlying section-scoped results.
- Improved grouped-label handling so duplicate heading names with different anchors still stay distinct.
- Updated the project README, main checklist, and a resumable slice checklist/refresh note for this vertical slice.
- Extended automated coverage for grouped helper behavior, grouped selection expansion, and duplicate-heading anchor handling.

## Tests and scans run
- `python3 -m unittest discover -s projects/markdown-notes-search -p 'test_*.py'`
- manual grouping self-test via `python3 - <<'PY' ... group_results_for_tui(...) ... PY`
- `python3 -m py_compile projects/markdown-notes-search/notes_search.py projects/markdown-notes-search/test_notes_search.py`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Review passes
1. Diff/readability review of grouped TUI state flow; kept grouped rows as a presentation layer over existing section results.
2. Edge-case review for duplicate section headings in the same note; fixed grouped labels to preserve distinct anchors.
3. Final publish-safety review; re-ran unit tests, helper self-test, compile checks, and the repo secret scan.

## Next step
- Add plain-text/export-side collapse controls so closely related section hits can be bundled outside the TUI too.
