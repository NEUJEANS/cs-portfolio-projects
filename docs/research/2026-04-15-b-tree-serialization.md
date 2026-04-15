# 2026-04-15 B-tree serialization research

## Goal
Add a storage-oriented slice to the B-tree lab without jumping all the way to fixed-size pages.

## Notes
- B-tree implementations used by databases/filesystems treat nodes as pages that can be materialized and restored later; a JSON snapshot is a reasonable portfolio-friendly stepping stone before binary page layouts.
- A useful first persistence slice should preserve tree shape, keys, values, and minimum degree so search/delete behavior stays reproducible after reload.
- Loading serialized state should validate structural invariants instead of trusting input blindly: sorted keys, unique keys, child count = key count + 1 for internal nodes, and node capacity bounds.
- Keeping the CLI able to save a tree from a dataset and then reload it demonstrates both construction and persistence in an interview-friendly workflow.

## Scope chosen for this run
- add `snapshot` output for tree inspection
- add `save PATH` command for persisted JSON output
- add `--tree-file` loading path with structure validation
- leave bulk loading and binary page encoding for later slices
