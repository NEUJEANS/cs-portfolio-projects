# 2026-04-15 suffix-tree-lab refresh: generalized suffix tree LCS

## Quick refresh
- Distinct sentinels per input string prevent synthetic cross-boundary matches.
- The candidate LCS should come from a node/path whose subtree contains suffixes from **both** source texts.
- Because this lab uses compressed edges, it is simpler to carry a running path string during DFS than to reconstruct it later.

## Self-test
Prompt: if a path contains a sentinel, can it still be a valid common substring across both texts?

Answer: no. Once a sentinel appears, that path has crossed a source boundary, so the candidate must be truncated before the sentinel.
