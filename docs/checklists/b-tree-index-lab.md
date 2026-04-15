# b-tree-index-lab Checklist

- [x] brief B-tree indexing research/refresh recorded
- [x] short Python `bisect` and tree-navigation self-test recorded
- [x] review current feature gaps against index-style workloads
- [x] implement nearest-key navigation helpers (`floor`, `ceil`, `neighbors`)
- [x] expose new commands in the CLI with JSON-friendly output
- [x] add automated tests for exact hit, gap lookup, edge cases, and CLI output
- [x] implement serialized tree snapshot/save/load support for page-level inspection
- [x] run at least 3 review passes and fix issues found
- [x] implement append-oriented bulk loading for strictly sorted datasets
- [x] expose a CLI switch for resumable sorted-dataset builds
- [x] add regression tests for bulk loading success and failure paths
- [x] benchmark sorted bulk loading against generic inserts and expose the comparison in the CLI
- [ ] future slice: fixed-size page encoding for more realistic on-disk pages
