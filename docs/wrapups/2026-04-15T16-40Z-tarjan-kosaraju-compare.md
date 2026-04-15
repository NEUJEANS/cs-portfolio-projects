# Wrap-up — Tarjan vs Kosaraju comparison slice

- **Timestamp:** 2026-04-15 16:40 UTC
- **Project:** `tarjan-scc-lab`
- **What changed:** added a deterministic Kosaraju SCC implementation, a `compare` CLI command with repeatable timing output, refreshed the README, added a sample comparison artifact, and expanded tests/review notes for the new workflow.
- **Tests run:**
  - `.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py` → 18 passed
  - `.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 2`
  - `.venv/bin/python -m pytest -q` → blocked by pre-existing duplicate-test import mismatch elsewhere in the repo (`projects/task-tracker-cli/tests/test_task_tracker.py`, `tests/test_interval_tree_lab.py`, `tests/test_task_tracker.py`)
- **Reviews run:** 3 documented passes with fixes for compare-path duplicate work, stale CLI scope text, and README timing-example accuracy.
- **Secret scan:** `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` → clean
- **Commit hash:** `63c200d`
- **Next step:** add SCC condensation bottleneck summaries (in-degree/out-degree) or topological-order groups in JSON for downstream tooling.
