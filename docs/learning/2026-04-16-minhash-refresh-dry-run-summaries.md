# MinHash dry-run refresh summary refresh

- A resumable refresh flow benefits from separating **diff planning** from **mutation**.
- For a saved index, compute four disjoint buckets: `reused`, `updated`, `added`, and `removed`.
- A dry-run path should reuse the same file-discovery logic as the real refresh, but must not rewrite timestamps or the index payload.
- Returning path-level lists in JSON makes large-corpus maintenance scriptable while keeping the human-readable CLI output short.
- Quick self-test: if one file changes, one is added, and one is deleted, the preview should show those exact paths and leave the index file byte-for-byte unchanged.
