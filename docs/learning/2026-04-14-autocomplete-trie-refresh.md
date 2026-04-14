# autocomplete-trie-cli refresh and self-test

## Refresh notes
- `heapq` min-heaps are good for top-k tracking by evicting the weakest current candidate.
- Trie nodes should track children, terminal-word metadata, and optionally subtree summary data.
- Fuzzy trie search can reuse Levenshtein DP rows: for each traversed character, derive a new row from the parent row.

## Self-test
1. Why keep `max_subtree_weight` on each node?
   - To prioritize or prune traversal when collecting top-ranked completions.
2. Why use DP rows instead of generating all words then comparing edit distance?
   - It avoids enumerating the full dictionary and keeps typo search bounded during traversal.
3. What is the practical ranking rule for fuzzy results?
   - Lower edit distance first, then higher weight, then word for deterministic ties.
