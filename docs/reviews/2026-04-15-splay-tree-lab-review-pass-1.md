# Review Pass 1 - splay-tree-lab

## Checks
- walked through insert/find/delete logic
- verified unsuccessful search splays the last visited node
- verified snapshot schema is minimal and resumable

## Fixes made
- ensured delete detaches left/right subtree parents before join
