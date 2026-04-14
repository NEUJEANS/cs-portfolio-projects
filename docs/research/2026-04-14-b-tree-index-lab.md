# B-tree index lab research

## Why this project
- B-trees are a classic systems/data-structures topic that maps well to database and filesystem indexing.
- A student portfolio benefits from showing balanced-tree logic, split handling, ordered traversal, and range queries.
- For a compact educational slice, an in-memory B-tree with a CLI and tests is a strong first milestone before persistence.

## Implementation notes used for this slice
- Use a configurable minimum degree `t`; internal nodes can hold `t-1` to `2t-1` keys.
- Split full children before descending during insertion so recursion only visits non-full nodes.
- Support ordered traversal and range queries because they show why B-trees are useful for index workloads.
- Keep duplicate key updates deterministic by replacing the existing value instead of storing duplicates.

## Future directions
- disk-page serialization and reloads
- bulk loading from sorted data
- deletion and merge/borrow rebalancing
- simple benchmark against binary-search over sorted arrays
