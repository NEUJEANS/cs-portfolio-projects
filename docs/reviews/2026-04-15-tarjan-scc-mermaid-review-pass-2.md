# Tarjan SCC Mermaid review pass 2

- Reviewed label safety and markdown portability.
- Issue found: node names containing double quotes could break Mermaid label syntax.
- Fix applied: added `_mermaid_escape()` and test coverage for quoted node identifiers.
