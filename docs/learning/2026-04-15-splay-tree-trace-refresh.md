# 2026-04-15 splay-tree trace refresh

## Refresher
- A splay tree does not store balance metadata; instead, every successful access or insertion splays the touched node toward the root.
- Useful teaching signal for this lab: root movement after each query is often more informative than the final inorder traversal.
- For a portable visualization artifact, Graphviz DOT is easier to diff and test than screenshots.

## Self-test
1. Why can a splay tree outperform a red-black tree on a hot set?
   - Repeatedly accessed keys move near the root, lowering future search depth for that workload.
2. Why export DOT instead of image files directly?
   - DOT is deterministic text, easy to version, easy to test, and can be rendered later with `dot`.
3. What should a good trace record per access?
   - hit/miss, root before/after, and the incremental cost such as rotations/comparisons.
