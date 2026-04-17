# network-flow-lab review pass 1 — 2026-04-16

## Focus
Dense benchmark-family generator audit.

## Issue found
The first dense-family draft added probabilistic backward edges between middle nodes, which meant some seeds could still produce a mostly forward-only graph. That weakened the intended residual-rerouting story.

## Fix
- added guaranteed backward middle-node chain edges in the dense generator
- kept optional extra backward edges on top for denser cyclic cases
- added regression coverage that checks the dense generator includes those backward edges

## Result
Dense benchmark runs now always include at least one clear residual-style rerouting path family instead of relying on luck.
