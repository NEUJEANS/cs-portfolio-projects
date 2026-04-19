# 2026-04-19 Aho-Corasick Stream Context Research

## Goal
Add small per-match excerpts to chunked Aho-Corasick searches without giving up bounded-memory streaming.

## Brief references checked
- Python `collections.deque` docs: useful for bounded append/pop behavior when keeping a rolling history window.
- Python `argparse` docs: no special parser tricks required; extending the existing `--context` option is the simplest CLI surface.

## Notes used for this slice
- a sampled context window only needs a small rolling history buffer of `max_pattern_length + context_chars`
- trailing context can be filled by keeping recently matched items in a short pending list until enough future characters arrive
- this approach preserves the streaming property: match excerpts are approximate local windows, not a signal to load the full file
- reusing `--context` is cleaner than inventing a second flag because users already understand it as “show nearby characters”
