# Tarjan SCC topology-groups self-test

Timestamp: 2026-04-16 10:41 UTC
Project: `tarjan-scc-lab`

## Why no extra web research
Grouping SCCs by condensation-DAG level is a direct extension of the project's existing `topology_level` metadata, so the slice can be implemented safely from the current code and graph-theory basics already in the repo.

## Quick refresh
- condensation DAG levels already tell us each SCC's longest-distance layer from any source SCC
- downstream tools should not need to rebuild grouped layers from a flat component list when the CLI can emit them directly
- deterministic ordering matters, so grouped components should preserve the same component order already used in the existing JSON outputs

## Self-test
1. If `C1` and `C2` both have `topology_level = 1`, should they appear in the same output group?  
   **Yes** — one `topology_groups` entry for level `1` with both components in deterministic order.
2. Should grouped entries duplicate the annotated component payload or only list component ids?  
   **Emit both** — keep the duplicated annotated payload for simple consumers and add lightweight `component_ids` for fast index-based renderers.
3. Should the grouped view be added only to `condensation` output?  
   **No** — also add it to `scc` summary JSON so both machine-facing entry points expose the same layered structure.
