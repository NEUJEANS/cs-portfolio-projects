# Review pass 2 — treap Mermaid export

- Scope reviewed: automated coverage for direct export and CLI file-writing behavior.
- Issue found: there was no explicit regression check for the empty-tree diagram case, which could silently degrade the UX for future refactors.
- Fix applied: added `test_empty_treap_mermaid_export_is_explicit`.
- Result: empty-state Mermaid output is now pinned by tests.
