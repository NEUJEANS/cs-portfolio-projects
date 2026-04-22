# avl-tree-lab checklist

- [x] define portfolio goals: insertion, deletion, validation, traversal, CLI, and trace output
- [x] refresh AVL invariants and the four rotation cases
- [x] implement node/tree structures with height metadata
- [x] implement insertion with LL/RR/LR/RL repair
- [x] implement deletion with successor replacement and rebalance-on-return
- [x] expose traversal, contains, rank, select, and validation helpers
- [x] add CLI commands for demo/build/contains/delete/rank/select/validate
- [x] document design and usage in README
- [x] add unit tests for all rotation families, deletion, validation, duplicates, and CLI output
- [x] maintain subtree sizes incrementally so `rank` and `select` stay `O(log n)`
- [x] add Graphviz DOT export with optional NIL leaves for portfolio diagrams
- [x] add `explain-trace` Markdown walkthrough export with initial/final DOT snapshots
- [x] cover subtree-size validation plus DOT/walkthrough CLI flows in tests
- [x] run at least 3 review passes and fix findings
- [x] add wrap-up note for this slice
