# 2026-04-15 Refresh — Python + KD-Tree Self-Test

## Quick refresh
- Median-based recursive construction keeps the tree reasonably balanced for static datasets.
- Pruning condition for nearest-neighbor search: after exploring the likely side, only inspect the far side if `axis_delta^2 <= best_distance`.
- For deterministic outputs, sort range-query results and break equal-distance nearest-neighbor ties consistently.

## Self-test
1. Why can nearest-neighbor search skip a far subtree?
   - Because if the squared distance to the split plane is already larger than the best known squared distance, no point in that subtree can improve the answer.
2. Why is KD-tree construction a good fit for immutable datasets?
   - A static median-built tree is simple and query-efficient, while dynamic balancing for frequent inserts/deletes is more complex.
3. Why still keep brute-force-comparable tests?
   - Pruning logic is easy to get subtly wrong; direct correctness checks anchor the implementation.
