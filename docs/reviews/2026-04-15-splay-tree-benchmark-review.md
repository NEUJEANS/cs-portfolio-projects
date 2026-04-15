# Splay Tree Benchmark Review — 2026-04-15

## Review pass 1 — execution and regression
- Ran `python3 -m unittest projects/splay-tree-lab/test_splay_tree_lab.py`.
- Found issue: dynamic import of `red_black_tree.py` failed during `@dataclass` processing because the temporary module was not registered in `sys.modules` before execution.
- Fix applied: register the module name before `exec_module`.
- Reran tests successfully.

## Review pass 2 — benchmark sanity
- Ran the new benchmark CLI with deterministic parameters.
- Confirmed the hot-set workload shows lower comparison counts for the splay tree than the red-black baseline.
- Confirmed the uniform-random workload can swing the other way, which makes the benchmark more honest and more useful in a portfolio discussion.

## Review pass 3 — docs and resumability
- Checked README, checklist, benchmark command discoverability, and supporting research/learning notes.
- Confirmed the slice explains why the comparison exists, how to rerun it, and what result to expect.
- Confirmed next unfinished items remain visible for future runs.
