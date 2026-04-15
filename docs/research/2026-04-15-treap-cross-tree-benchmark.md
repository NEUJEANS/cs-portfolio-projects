# 2026-04-15 treap cross-tree benchmark research

## Goal
Add a portfolio-facing benchmark slice for `treap-order-statistics-lab` that compares treap behavior with the repo's AVL, red-black, and splay tree labs.

## Notes
- Treaps have expected `O(log n)` height because random priorities make the shape behave like a random BST.
- AVL trees should stay shortest under deterministic insertion orders because they enforce stricter balance.
- Red-black trees usually trade a little extra height for fewer balancing constraints than AVL.
- Splay trees are best framed with amortized access behavior rather than static height; a lookup benchmark should report comparison and rotation costs because each query reshapes the tree.
- For a deterministic repo artifact, benchmark inputs should use fixed ascending/descending/shuffled insertion orders and a seeded successful-query workload.

## Sources
- CMU treap notes: https://www.cs.cmu.edu/afs/cs/academic/class/15210-f25/www/algobook/bsts/treaps.pdf
- USACO treap guide: https://usaco.guide/adv/treaps
- existing repo implementations in `projects/avl-tree-lab`, `projects/red-black-tree-lab`, and `projects/splay-tree-lab`
