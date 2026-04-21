# 2026-04-21 consistent-hashing visualization review pass 2

## Focus
Inspect ring readability for medium-sized virtual-node counts that are realistic for portfolio screenshots.

## Issue found
- With 128 virtual points in the sample artifact, the original point radius made the outer ring look too dense and slightly muddy.

## Fix applied
- Switched the SVG renderer to use adaptive point radii so small rings stay legible while denser rings use smaller dots.
- Kept the same geometry and colors so the artifact remains deterministic.

## Verification
- `python3 -m unittest projects/consistent-hashing-lab/test_consistent_hashing.py`
- `python3 projects/consistent-hashing-lab/consistent_hashing.py visualize --nodes node-a node-b node-c node-d --key-count 24 --displayed-key-count 12 --virtual-nodes 32 --replication-factor 2 --title 'Consistent hashing ring with replica placement' --svg-out /tmp/consistent-hashing-ring.svg --html-out /tmp/consistent-hashing-ring.html`
