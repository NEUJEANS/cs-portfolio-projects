# B-tree index lab deletion slice research

## Goal
Add a meaningful second systems/data-structures slice to the in-memory B-tree lab by implementing deletion safely, not just insertion and range scans.

## Notes used for this slice
- B-tree deletion is portfolio-worthy because it exercises the harder maintenance cases: deleting from leaves, deleting from internal nodes, borrowing from siblings, merging underfull nodes, and shrinking the root.
- A compact educational implementation should keep the classic minimum-degree `t` invariants visible in code.
- Internal-node deletes can replace the removed key with either the predecessor from the left subtree or the successor from the right subtree when that child has enough keys.
- If both adjacent children are minimal, merge them with the separator key before continuing.
- Before descending during delete, ensure the chosen child has at least `t` keys so recursion does not enter an underfull node.

## Slice boundary
Keep this pass in-memory and CLI-driven. Leave page serialization/persistence for a future run.
