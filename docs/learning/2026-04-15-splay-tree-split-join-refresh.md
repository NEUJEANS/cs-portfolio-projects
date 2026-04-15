# Splay Tree Split/Join Refresh — 2026-04-15

## Focus
- refresh how splay-tree split works when the pivot is present vs missing
- refresh the standard join precondition: every key in the left tree must be smaller than every key in the right tree
- sanity-check the CLI UX for success and invalid-range failures

## Quick notes
- `split(pivot)` can be implemented by splaying the last accessed node to the root.
  - if `pivot` exists at the root after splaying, detach `root.left` and `root.right`
  - if the root key is `< pivot`, the root belongs to the left partition and its right child becomes the right partition
  - if the root key is `> pivot`, the root belongs to the right partition and its left child becomes the left partition
- `join(left, right)` is valid only when `max(left) < min(right)`.
  - splay the maximum node in the left tree to the root
  - attach the right tree as `root.right`

## Self-test
- checked split around a present pivot (`12`) and a missing pivot (`11`)
- checked join on disjoint ranges and invalid overlapping ranges
- confirmed invalid join input now exits with a clean CLI error message instead of a traceback
