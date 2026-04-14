# Review pass 2 — b-tree-index-lab neighbors slice

## Focus
README/demo audit plus CLI smoke-test coverage.

## Findings
1. README usage examples showed `neighbors` and `floor` but skipped `ceil`, leaving the feature set partially documented.
2. Test coverage exercised `neighbors` CLI output but did not explicitly cover the null-return edge case for `floor` when no lower key exists.

## Fixes applied
- Added a `ceil` example to the README usage block.
- Added a CLI regression test asserting `floor 0` returns JSON `{ "key": 0, "item": null }`.

## Status
- Docs and edge-case coverage improved.
