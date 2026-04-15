# Review pass 1 — treap Mermaid export

- Scope reviewed: new `to_mermaid()` implementation and CLI wiring.
- Issue found: the slice produced a diagram file, but the README did not point readers to the committed example artifact or note that the root shape depends on the seed.
- Fix applied: updated the README Mermaid section to mention reproducible seeds and the committed sample `docs/artifacts/treap-order-statistics-mermaid.mmd`.
- Result: documentation now matches the new export workflow.
