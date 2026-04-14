# Review Pass 1 — Aho-Corasick Search Lab

## Checks
- executed `python3 projects/aho-corasick-search-lab/test_aho_corasick_search.py`

## Issue found
- JSON serialization used `match.__dict__`, which fails for slot-based dataclasses.

## Fix applied
- switched to `dataclasses.asdict(match)` in `search_text()`.

## Result
- test suite passed after the fix.
