# 2026-04-19 Aho-Corasick Stream Context Refresh

## Refresher
- Aho-Corasick already carries automaton state across chunks, so cross-boundary matching does not need manual overlap rereads.
- To reconstruct a small excerpt at match time, keep only the recent raw characters needed for `context_before + pattern_text`.
- To fill `context_after`, keep a short pending queue of matches until enough future characters arrive.
- This is a bounded-memory UX feature, not a second search pass.

## Quick self-test
1. Why is the rolling history buffer larger than just `context_chars`? Because a match may start before its last character is seen, so the buffer must still contain the full matched pattern plus the requested left context.
2. Why can chunked mode emit partial right context at end-of-file? Because the stream may end before the requested after-window fills, and the best bounded-memory answer is “whatever characters actually arrived.”
3. Why reuse `--context` instead of adding `--sampled-context`? The UX meaning is the same; only the internal implementation changes between memory and streaming modes.
