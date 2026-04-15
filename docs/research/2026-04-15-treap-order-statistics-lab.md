# Treap order-statistics lab research

## Brief external notes
- Treaps combine BST ordering on keys with heap ordering on randomly assigned priorities.
- Split and merge are the key primitive operations; insert/delete can be reduced to those helpers.
- With independent random priorities, expected height stays logarithmic, making treaps a compact alternative to deterministic balanced trees.
- Maintaining subtree sizes enables rank/select queries without changing the split/merge model.

## Portfolio angle
- good follow-up to the repo's AVL, red-black, and splay tree labs because it demonstrates a different balancing strategy
- interview-friendly because it is short, elegant, and easy to compare against rotation-heavy trees
- strong teaching value: randomness, invariants, expected complexity, and order-statistics in one project

## Slice choice
Build a compact Python lab with seeded reproducibility, validation, CLI demos, and tests for insert/delete/rank/select/range-count.
