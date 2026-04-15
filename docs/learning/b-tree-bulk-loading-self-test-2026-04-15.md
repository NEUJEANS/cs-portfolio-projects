# B-tree bulk loading self-test — 2026-04-15

## Refresh
- In a sorted insert stream, every new key descends to the rightmost path.
- The main correctness risk is splitting a full node before descending so the leaf still has room for the append.
- Reusing the existing split routine is safer than inventing a second structural balancing path.

## Quick self-test
1. **Question:** If the root is full before appending the next largest key, what happens first?
   - **Answer:** Split the root, create a new internal root, then continue down the rightmost child.
2. **Question:** Why can leaf insertion skip `bisect_left` in sorted bulk-load mode?
   - **Answer:** The new key is guaranteed to be greater than every previous key, so it belongs at the end.
3. **Question:** Why reject duplicates in `bulk_load_sorted`?
   - **Answer:** The fast path assumes a strictly increasing stream; allowing duplicates would require update semantics that break the append-only invariant.
