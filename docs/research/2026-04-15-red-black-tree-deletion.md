# Research — 2026-04-15 red-black-tree deletion slice

## Question
What is the safest portfolio-friendly way to add deletion to the existing red-black tree lab without breaking subtree-size augmentation?

## Notes
- Red-black deletion starts like ordinary BST deletion: remove the target directly if it has at most one child, otherwise swap structural position with the inorder successor and delete the successor node instead.
- The hard part is deleting a black node. That can create a temporary "double black" deficit on the replacement path, so the repair logic needs sibling-color case handling plus recoloring/rotations.
- Null leaves can be treated as black in the case analysis, which keeps a pointer-based Python implementation manageable without introducing a full sentinel object.
- Order-statistics augmentation remains `O(log n)` as long as subtree sizes are refreshed after transplants, rotations, and upward path changes.

## Implementation direction chosen
- keep the existing explicit `None` leaf representation
- add a `delete()` API that reuses inorder-successor replacement for two-child deletes
- track replacement parent/side information so delete-fixup still works when the replacement child is `None`
- refresh `subtree_size` metadata on affected ancestors after structural edits and again after repair rotations if needed

## Sources consulted
- Gemini web search summary for: `red-black tree deletion cases double black inorder successor subtree size augmentation summary`
- cited references surfaced by search included Wikipedia, Programiz, Wits lecture notes, and UChicago deletion notes
