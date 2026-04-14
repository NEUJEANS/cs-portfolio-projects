# Consistent Hashing Replication Slice Research — 2026-04-14

## Goal
Upgrade `consistent-hashing-lab` from single-owner placement to portfolio-ready replicated placement.

## Notes
- A practical consistent-hashing system usually selects multiple distinct physical nodes for redundancy instead of only the first clockwise match.
- With virtual nodes, replication should skip duplicate physical owners so a single server is not selected twice through different virtual-node positions.
- Useful portfolio outputs: per-key replica sets, replication-aware distribution counts, and topology remap summaries that show how many replica placements changed after adding/removing a node.

## Implementation direction
- Add `get_nodes(key, replication_factor)` to walk clockwise until it finds distinct physical nodes.
- Keep `get_node(key)` as a compatibility wrapper for replication factor 1.
- Extend CLI with `--replication-factor` for `assign`, `report`, and `remap`.
- In reports, include per-node replica ownership counts and average/max replica load.
- In remap simulation, compare sorted replica sets per key and count replica placement changes.
