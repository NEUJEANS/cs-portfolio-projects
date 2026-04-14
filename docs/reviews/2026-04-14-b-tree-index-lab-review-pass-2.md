# Review pass 2 - test/runtime audit

## Checks
- ran `python3 -m unittest projects/b-tree-index-lab/test_btree_index.py`
- ran CLI smoke test with `--json range 10 50`
- inspected test isolation behavior

## Issues found
- test CLI fixture wrote data into a persistent temp folder under the project tree

## Fix applied
- switched the CLI test to `tempfile.TemporaryDirectory()` so the test leaves no residue
