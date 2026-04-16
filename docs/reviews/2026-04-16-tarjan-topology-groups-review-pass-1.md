# Tarjan topology-groups review pass 1

- Focus: JSON shape usefulness for downstream tooling.
- Checked: `topology_groups` payload structure in `condensation` and `scc` output.
- Issue found: grouped output duplicated full component payloads but did not expose a lightweight ordered id list, which would make simple renderers or link builders do extra traversal work.
- Fix applied: added `component_ids` to every topology group and updated tests/README expectations accordingly.
