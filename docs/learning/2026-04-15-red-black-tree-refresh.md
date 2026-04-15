# 2026-04-15 red-black-tree refresh

## Quick refresh
- red-black trees maintain near-balanced height with five invariants: every node is red or black, root is black, NIL leaves are black, red nodes cannot have red children, and every path to a NIL leaf has the same black height.
- insertion starts like BST insertion with the new node colored red.
- fix-up resolves only red-parent violations using three case families: recolor when the uncle is red, rotate inward cases to convert them into outer cases, then rotate/recolor around the grandparent.
- the height stays `O(log n)` because the longest root-to-leaf path is at most twice the shortest black-only path.

## Self-test
1. Why insert red instead of black?
   - Inserting red preserves existing black heights; only red-red violations may need repair.
2. What happens when parent and uncle are red?
   - Recolor parent and uncle black, grandparent red, then continue from the grandparent.
3. Why force the root black at the end?
   - Recoloring can move a red violation to the root; the final step restores the root-black invariant cleanly.
