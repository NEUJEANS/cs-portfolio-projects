# Splay tree benchmark-series refresh — 2026-04-16

## Quick refresh
- Keep benchmark output deterministic by deriving each series entry from a stable base seed plus the entry index.
- Reuse the single-size benchmark payload shape inside the series output so future docs/report generators can compose from one source of truth.
- Flatten CSV rows by `(series_index, size, workload)` so chart tooling can group by size or workload without extra preprocessing.

## Self-test
- `python3 -m unittest projects/splay-tree-lab/test_splay_tree_lab.py`
- `python3 projects/splay-tree-lab/splay_tree_lab.py benchmark-series 63 127 255 --hot-set-size 8 --hot-queries 256 --random-queries 256 --seed 42 --json-output artifacts/splay-tree-benchmark-series.json --csv-output artifacts/splay-tree-benchmark-series.csv`
