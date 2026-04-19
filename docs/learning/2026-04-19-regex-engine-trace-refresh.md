# Regex engine trace refresh and self-test — 2026-04-19

## Refresh
- fullmatch tracing should start from the epsilon-closed start state set at position 0, then record one consume step per input character, then a final closure check for `$` / `MATCH`
- search tracing is slightly different: it retries start offsets left-to-right unless the pattern is anchored with `^`, and it should stop on the first start offset that yields a match
- the most useful transition payload is not every epsilon edge but the concrete matching states that consumed the current character and their outgoing targets before the next closure expands

## Self-test
1. Why keep `trace` JSON-first instead of jumping straight to HTML?
   - JSON is easy to test, easy to diff, and becomes the durable source for future visualizers.
2. Where should `MATCH` appear in a trace?
   - in the active/closure state set after epsilon expansion, never as a character-consuming transition.
3. What makes a search trace educational instead of noisy?
   - showing each attempted start offset and the winning leftmost match, not just the final substring.
