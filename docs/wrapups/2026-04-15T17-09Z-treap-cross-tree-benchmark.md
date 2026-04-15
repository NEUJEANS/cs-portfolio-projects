# Wrap-up — 2026-04-15T17:09Z treap cross-tree benchmark

- timestamp: 2026-04-15T17:09Z
- project: `treap-order-statistics-lab`
- commit: `e444376`

## What changed
- added a `benchmark` CLI command to compare treap build/query behavior with the repo's AVL, red-black, and splay tree labs
- exported deterministic benchmark data to `artifacts/treap-vs-balanced-trees.csv`
- updated the treap README with benchmark usage, artifact output, and sample findings
- expanded unit tests to cover benchmark helpers, CSV export, and CLI benchmark flows
- logged resumable research, refresh, checklist, and three review passes for this slice

## Tests and reviews run
- `python3 -m unittest projects/treap-order-statistics-lab/test_treap_order_statistics_lab.py tests/test_red_black_tree_lab.py`
- `python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 7 benchmark --count 31 --queries 48 --query-seed 23 --csv --csv-file artifacts/treap-vs-balanced-trees.csv`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review logs:
  - `docs/reviews/2026-04-15-treap-cross-tree-benchmark-review-pass-1.md`
  - `docs/reviews/2026-04-15-treap-cross-tree-benchmark-review-pass-2.md`
  - `docs/reviews/2026-04-15-treap-cross-tree-benchmark-review-pass-3.md`

## Next step
- extend the benchmark from successful lookups to mixed insert/delete/query workloads so the treap's split/merge ergonomics can be compared under churn, not just static trees
