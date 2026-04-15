# Treap Mermaid export slice — 2026-04-15 23:27 UTC

## What changed
- added `export-mermaid` to `projects/treap-order-statistics-lab/treap_order_statistics_lab.py`
- implemented `Treap.to_mermaid()` with key / priority / subtree-size labels plus dotted null-child edges
- updated the treap README with Mermaid usage and reproducibility notes
- added regression tests for direct Mermaid export, empty-tree output, and CLI file writing
- generated and committed `docs/artifacts/treap-order-statistics-mermaid.mmd`
- added a resumable checklist and three review-pass notes for this slice

## Tests and reviews run
- `.venv/bin/python -m unittest projects/treap-order-statistics-lab/test_treap_order_statistics_lab.py`
- review pass 1: docs/artifact usability audit
- review pass 2: empty-state regression coverage audit
- review pass 3: CLI smoke run and generated artifact audit
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit
- `c6f64738bd7ff04fc298365f79ef3c80489c621c`

## Next step
- add split/merge trace overlays or operation-step snapshots on top of the Mermaid export so the treap balancing story is visible during inserts and deletes.
