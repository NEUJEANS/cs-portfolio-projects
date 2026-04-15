# red-black-tree trace refresh — 2026-04-15

## Quick refresh
- Insertion usually collapses into three explainable buckets: recolor, triangle rotation, and line rotation.
- Deletion repair is easier to debug when phrased around sibling color plus whether the sibling's inner/outer children are red or black.
- If trace labels mirror those conceptual buckets, the output is teachable and stable under tests.

## Self-check
- Can the tree still validate after traced insertions? yes
- Can the tree still validate after traced deletions? yes
- Can the CLI expose trace without changing default output? yes
