# AVL Tree Trace Walkthrough (delete)

- delete query: `10`
- deleted: `10`
- input: `[20, 10, 30, 5, 15, 25, 35]`
- size: `6`
- height: `3`
- valid: `True`

## Tree snapshots

### Initial DOT

```dot
digraph AVLTree {
  graph [rankdir=TB, nodesep=0.35, ranksep=0.45];
  node [shape=circle, style=filled, fontname="Helvetica", fillcolor="#1f6feb", fontcolor=white, penwidth=1.2];
  edge [arrowsize=0.7, color="#57606a"];
  node_root [label="20\nh=3\nsize=7\nb=0"];
  node_root -> node_rootl [label="L"];
  node_rootl [label="10\nh=2\nsize=3\nb=0"];
  node_rootl -> node_rootll [label="L"];
  node_rootll [label="5\nh=1\nsize=1\nb=0"];
  nil_1_rootlll [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootll -> nil_1_rootlll [label="L"];
  nil_2_rootllr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootll -> nil_2_rootllr [label="R"];
  node_rootl -> node_rootlr [label="R"];
  node_rootlr [label="15\nh=1\nsize=1\nb=0"];
  nil_3_rootlrl [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootlr -> nil_3_rootlrl [label="L"];
  nil_4_rootlrr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootlr -> nil_4_rootlrr [label="R"];
  node_root -> node_rootr [label="R"];
  node_rootr [label="30\nh=2\nsize=3\nb=0"];
  node_rootr -> node_rootrl [label="L"];
  node_rootrl [label="25\nh=1\nsize=1\nb=0"];
  nil_5_rootrll [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrl -> nil_5_rootrll [label="L"];
  nil_6_rootrlr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrl -> nil_6_rootrlr [label="R"];
  node_rootr -> node_rootrr [label="R"];
  node_rootrr [label="35\nh=1\nsize=1\nb=0"];
  nil_7_rootrrl [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrr -> nil_7_rootrrl [label="L"];
  nil_8_rootrrr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrr -> nil_8_rootrrr [label="R"];
}
```

### Final DOT

```dot
digraph AVLTree {
  graph [rankdir=TB, nodesep=0.35, ranksep=0.45];
  node [shape=circle, style=filled, fontname="Helvetica", fillcolor="#1f6feb", fontcolor=white, penwidth=1.2];
  edge [arrowsize=0.7, color="#57606a"];
  node_root [label="20\nh=3\nsize=6\nb=0"];
  node_root -> node_rootl [label="L"];
  node_rootl [label="15\nh=2\nsize=2\nb=1"];
  node_rootl -> node_rootll [label="L"];
  node_rootll [label="5\nh=1\nsize=1\nb=0"];
  nil_1_rootlll [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootll -> nil_1_rootlll [label="L"];
  nil_2_rootllr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootll -> nil_2_rootllr [label="R"];
  nil_3_rootlr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootl -> nil_3_rootlr [label="R"];
  node_root -> node_rootr [label="R"];
  node_rootr [label="30\nh=2\nsize=3\nb=0"];
  node_rootr -> node_rootrl [label="L"];
  node_rootrl [label="25\nh=1\nsize=1\nb=0"];
  nil_4_rootrll [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrl -> nil_4_rootrll [label="L"];
  nil_5_rootrlr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrl -> nil_5_rootrlr [label="R"];
  node_rootr -> node_rootrr [label="R"];
  node_rootrr [label="35\nh=1\nsize=1\nb=0"];
  nil_6_rootrrl [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrr -> nil_6_rootrrl [label="L"];
  nil_7_rootrrr [label="NIL", shape=box, width=0.35, height=0.2, fontsize=10, fillcolor="#d1d9e0", fontcolor="#24292f"];
  node_rootrr -> nil_7_rootrrr [label="R"];
}
```

## Event-by-event explanation

1. delete key 10
2. replace 10 with successor 15
3. delete key 15

## Final state

- root: `{'key': 20, 'height': 3, 'subtree_size': 6, 'balance': 0}`
- inorder traversal: `[5, 15, 20, 25, 30, 35]`
- validation issues: `[]`
