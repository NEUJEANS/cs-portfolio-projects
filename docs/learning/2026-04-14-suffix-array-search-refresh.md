# suffix-array-search-lab refresh + self-test

## Refresh
- Python's `bisect` works on precomputed comparable values, but custom suffix-prefix comparison is easier to express with hand-rolled lower/upper-bound binary search.
- For substring search, compare only `text[start:start+len(pattern)]` against the pattern.
- Context windows are easiest to generate from the original text after match positions are known.
- Line numbers can be derived efficiently from precomputed line-start offsets and `bisect_right`.

## Self-test
1. Why do two binary searches suffice to find all matches?
   - Because matching suffixes are contiguous in lexicographic order.
2. What should the comparison key be during search?
   - The suffix prefix of length `len(pattern)`, not the full suffix.
3. Why store the original text in the index file?
   - To generate context windows and line-number lookups without rebuilding from source.
