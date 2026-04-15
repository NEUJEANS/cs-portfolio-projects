# Tarjan SCC Mermaid review pass 1

- Reviewed the first Mermaid export implementation against the existing DOT export.
- Issue found: the renderer did a repeated linear search (`next(...)`) for every component within each level block.
- Fix applied: precomputed `summary_by_id` so Mermaid rendering stays clean and linear in the number of SCCs.
