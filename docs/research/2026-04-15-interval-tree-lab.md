# 2026-04-15 interval-tree-lab research note

## Goal
Add another strong data-structure project that is more practical than a plain BST and different enough from the existing tree/index set.

## Why interval trees fit the portfolio
- classic CS topic with real use in calendars, reservation systems, compiler live ranges, genomic coordinates, and collision windows
- lets the repo demonstrate augmentation: storing extra subtree metadata to accelerate queries
- has a tight vertical slice: immutable interval model, overlap search, point stabbing queries, validation, CLI, and tests

## Design chosen for this slice
- use a BST ordered by interval `(start, end, label)`
- augment every node with `max_end`, the largest interval end value in its subtree
- use `max_end` during search to skip left subtrees that cannot possibly overlap the query
- treat intervals as closed ranges, so endpoint-touching intervals overlap
- bulk-build from sorted unique intervals using median splits to keep the initial tree compact and deterministic for demos

## Scope intentionally left for future slices
- deletion and rebalancing
- trace visualization / Graphviz export
- benchmarks versus naive scanning

## Notes
This slice uses standard interval-tree ideas from classic algorithms references and interview literature. Web search was attempted but unavailable during this run, so the implementation sticks to well-known overlap-search invariants rather than adding fragile external claims.
