# Review log — avl-tree-lab Graphviz + trace export slice — 2026-04-22

## Pass 1 — code-path review
- Reviewed the new summary/export flow after adding subtree-size metadata.
- Issue found: `summary()` reported `height()` from stored node metadata, which could hide height drift if a corruption bug slipped in.
- Fix: switched summary height to the recomputed validated height so exported payloads stay trustworthy even when validation is surfacing metadata issues.

## Pass 2 — docs and CLI discoverability review
- Reviewed the README against the new `dot` command behavior.
- Issue found: the first README update showed DOT export but did not mention the `--no-nil` compact-diagram flag.
- Fix: added a short README note so users can choose between explicit NIL-heavy teaching diagrams and cleaner portfolio screenshots.

## Pass 3 — artifact pack review
- Smoke-tested committed artifacts and compared regenerated outputs to the checked-in files.
- Issue found: the sample artifact pack only covered delete traces, which left the insertion-rotation story less inspectable.
- Fix: added committed `build-trace.md` and `build-trace.json` artifacts alongside the delete walkthrough and DOT sample.

## Validation run after fixes
- `python3 -m py_compile projects/avl-tree-lab/avl_tree_lab.py projects/avl-tree-lab/test_avl_tree_lab.py`
- `python3 -m unittest projects/avl-tree-lab/test_avl_tree_lab.py -v`
- `python3 projects/avl-tree-lab/avl_tree_lab.py dot 30 20 10 25 40 50 --output /tmp/avl-demo.dot`
- `python3 projects/avl-tree-lab/avl_tree_lab.py explain-trace build 30 20 10 25 40 --output /tmp/avl-build-trace.md`
- `python3 projects/avl-tree-lab/avl_tree_lab.py explain-trace delete 20 10 30 5 15 25 35 --query 10 --output /tmp/avl-delete-trace.md`
- `cmp -s /tmp/avl-demo.dot docs/artifacts/avl-tree-lab/demo.dot`
- `cmp -s /tmp/avl-build-trace.md docs/artifacts/avl-tree-lab/build-trace.md`
- `cmp -s /tmp/avl-delete-trace.md docs/artifacts/avl-tree-lab/delete-trace.md`
- `git diff --check`
