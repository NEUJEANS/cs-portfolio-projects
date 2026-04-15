# 2026-04-15 splay-tree trace + DOT slice

## Goal
Add a resume-friendly visualization slice to `splay-tree-lab` so a student can show how access patterns reshape the tree, not just quote amortized complexity.

## Checklist
- [x] inspect current `splay-tree-lab` implementation and identify the weakest missing demo surface
- [x] confirm the repo is in sync with `origin/main` before editing
- [x] add step-by-step access tracing with per-query root/rotation/comparison metrics
- [x] add Graphviz DOT export for tree snapshots with highlighted access keys
- [x] expose the feature through a CLI command that can save before/after diagrams
- [x] update README usage and feature notes
- [x] add/expand automated tests for behavior and CLI flows
- [x] run targeted tests and then the repo test suite
- [x] log at least 3 review passes and fix issues found
- [x] run a secret scan before push
