# Tarjan SCC Mermaid refresh

- Mermaid flowcharts accept quoted node labels, so HTML `<br/>` line breaks work well for multi-line SCC summaries in markdown.
- Grouping SCCs into per-level `subgraph` blocks mirrors the existing condensation `topology_level` metadata and keeps layouts deterministic enough for docs demos.
- Quick self-test used before coding:
  - `C0["C0<br/>level=0 | size=3<br/>A, B, C"] --> C1["C1"]`
  - escape embedded double quotes in labels so arbitrary node names do not break Mermaid markup.
