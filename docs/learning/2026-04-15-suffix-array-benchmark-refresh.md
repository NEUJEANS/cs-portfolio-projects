# 2026-04-15 suffix-array benchmark refresh

## Quick research takeaway
- A suffix array keeps suffix start offsets sorted lexicographically, so substring lookup can use binary search instead of traversing explicit tree edges.
- A straightforward educational implementation can build the array by sorting all suffix starts with `text[start:]` as the key; that is not asymptotically optimal, but it is compact and easy to explain in interviews.
- Naive suffix-array searching is typically discussed as `O(m log n)` comparisons for a pattern of length `m`, while suffix trees keep query traversal linear in the pattern once the index exists.
- In practice, suffix arrays are often easier to serialize and benchmark against tree-based indexes because the structure is just an ordered list of offsets.

## Self-test
- If the sorted suffixes for `banana` begin with `$`, `a$`, `ana$`, `anana$`, `banana$`, `na$`, `nana$`, then the suffix-array offsets should be `[6, 5, 3, 1, 0, 4, 2]`.
- Binary-search lookup for `ana` should land on the contiguous suffix range rooted at offsets `1` and `3`.
- A benchmark baseline should reuse the built suffix array across lookups so the timing stays focused on query cost, not index construction.
