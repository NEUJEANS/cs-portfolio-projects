# Review pass 1 — suffix-array-search-lab

- Checked algorithm flow and CLI ergonomics.
- Issue found: search arguments accepted negative context and zero/negative limit values, which could produce confusing output or silent misuse.
- Fix applied: added validated integer parsers plus explicit runtime validation in `keyword_in_context`.
