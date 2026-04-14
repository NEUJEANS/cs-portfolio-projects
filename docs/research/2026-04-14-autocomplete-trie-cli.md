# autocomplete-trie-cli research

## Goal
Add a portfolio project that demonstrates a classic CS data structure with a practical search workflow.

## Brief findings
- A trie is a strong fit for prefix lookup because it shares prefixes and makes completions easy to enumerate.
- A weighted suggestion system is more realistic than plain lexicographic output; rankings should favor higher-frequency terms.
- Typo-tolerant search is a meaningful vertical slice. A practical approach is dynamic-programming traversal over trie branches with a bounded Levenshtein distance.
- For a student portfolio, the most useful scope is: weighted prefix search + bounded fuzzy search + CLI + tests + sample dataset.

## Chosen slice
Build a Python CLI that:
1. loads word,weight pairs from a CSV-like text file
2. returns top-k weighted prefix completions
3. optionally falls back to fuzzy matches within a bounded edit distance
4. prints clear sections for exact prefix results and fuzzy suggestions
5. remains standard-library only

## Notes for implementation
- Store subtree max weight at each node to make top-k prefix traversal more obviously purposeful.
- Use a min-heap for top-k collection and sort descending for output.
- Use row-by-row dynamic programming when traversing the trie for fuzzy matches.
