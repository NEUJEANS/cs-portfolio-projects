# 2026-04-15 red-black-tree DOT refresh

## Brief research
- Graphviz tree diagrams read better when parent->child edges are emitted in deterministic left/right order.
- Rendering NIL leaves as small dark placeholder nodes helps explain black-height and deletion repair cases in red-black trees.
- Labeling edges with `L`/`R` makes screenshots and interview walkthroughs easier to narrate.

## Self-test
- Confirmed the current implementation already tracks color and subtree size per node, so DOT labels can surface both balancing state and order-statistics metadata.
- Chose JSON-wrapped DOT output via a new CLI subcommand so the project keeps its existing machine-readable interface style.
