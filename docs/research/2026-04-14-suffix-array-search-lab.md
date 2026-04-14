# suffix-array-search-lab research notes

Date: 2026-04-14

## Goal
Build a portfolio-friendly text indexing project that demonstrates classic string algorithms instead of CRUD.

## Brief findings
- A suffix array stores the starting indices of all suffixes in lexicographic order.
- Substring search can be done with binary search over the sorted suffixes.
- All suffixes beginning with a pattern form a contiguous range, so lower/upper-bound searches return all hits.
- Keyword-in-context (KWIC) output is a natural user-facing feature for demos because it shows the hit plus nearby text.

## Slice choice
Implement a Python CLI that:
1. builds a suffix-array index for a text file,
2. saves the index as JSON,
3. searches for substring matches with binary search,
4. prints context windows and optional line numbers.

## Sources consulted
- Princeton Algorithms, suffix arrays / KWIC overview
- Yale CS notes on suffix arrays
- general suffix-array binary-search references surfaced by web search
