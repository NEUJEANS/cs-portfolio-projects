# AVL Tree Trace Walkthrough (build)

- input: `[30, 20, 10, 25, 40]`
- size: `5`
- height: `3`
- valid: `True`

## Tree snapshots

### Initial DOT

```dot
digraph AVLTree {
  graph [rankdir=TB, nodesep=0.35, ranksep=0.45];
  node [shape=circle, style=filled, fontname="Helvetica", fillcolor="#1f6feb", fontcolor=white, penwidth=1.2];
  edge [arrowsize=0.7, color="#57606a"];
  empty [label="∅", shape=plaintext, fontcolor=black];
}
```

### Final DOT

```dot
digraph AVLTree {
  graph [rankdir=TB, nodesep=0.35, ranksep=0.45];
  node [shape=circle, style=filled, fontname="Helvetica", fillcolor="#1f6feb", fontcolor=white, penwidth=1.2];
  edge [arrowsize=0.7, color="#57606a"];
  node_root [label="20\nh=3\nsize=5\nb=-1"];
  node_root -> node_rootl [label="L"];
  node_rootl [label="10\nh=1\nsize=1\nb=0"];
  nil_1_rootll [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootl -> nil_1_rootll [label="L"];
  nil_2_rootlr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootl -> nil_2_rootlr [label="R"];
  node_root -> node_rootr [label="R"];
  node_rootr [label="30\nh=2\nsize=3\nb=0"];
  node_rootr -> node_rootrl [label="L"];
  node_rootrl [label="25\nh=1\nsize=1\nb=0"];
  nil_3_rootrll [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrl -> nil_3_rootrll [label="L"];
  nil_4_rootrlr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrl -> nil_4_rootrlr [label="R"];
  node_rootr -> node_rootrr [label="R"];
  node_rootrr [label="40\nh=1\nsize=1\nb=0"];
  nil_5_rootrrl [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrr -> nil_5_rootrrl [label="L"];
  nil_6_rootrrr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrr -> nil_6_rootrrr [label="R"];
}
```

## Event-by-event explanation

1. insert leaf 30
2. insert leaf 20
3. insert leaf 10
4. insert 10: right rotation at 30
5. insert leaf 25
6. insert leaf 40

## Final state

- root: `{'key': 20, 'height': 3, 'subtree_size': 5, 'balance': -1}`
- inorder traversal: `[10, 20, 25, 30, 40]`
- validation issues: `[]`
