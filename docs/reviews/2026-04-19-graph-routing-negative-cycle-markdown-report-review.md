# Graph routing negative-cycle lab Markdown report review — 2026-04-19

## Pass 1 — implementation audit
- Reviewed the new Markdown export path end to end (`render_markdown`, `export_markdown`, CLI wiring, unreachable fixture flow).
- Issue found: Markdown table cells were written raw, so node labels containing `|` or embedded newlines could corrupt the exported table.
- Fix applied: added `_escape_markdown_cell(...)` and routed all Markdown table headers/cells through it.
- Validation: added `test_export_markdown_escapes_pipe_characters_in_cells`.

## Pass 2 — algorithm/data-shape audit
- Reviewed the negative-cycle reachability helper and path-status annotations for scalability/readability.
- Issue found: `_nodes_reachable_from_starts(...)` used `list.pop(0)`, which makes the traversal unnecessarily quadratic on larger graphs.
- Fix applied: switched the traversal queue to `collections.deque` with `popleft()`.
- Validation: reran the focused lab test suite and regenerated the checked-in unreachable report artifact.

## Pass 3 — smoke/docs audit
- Reviewed README commands, checked-in artifact output, and test breadth.
- Result: project-local docs/artifacts matched the implemented CLI.
- Broader smoke note: a full repo `pytest -q` attempt still hits pre-existing collection problems outside this slice (`projects/interval-tree-lab/test_interval_tree_lab.py` import mismatch / missing symbol and duplicate `test_task_tracker` collection collisions). These were not introduced by the graph-routing changes, so this slice used focused coverage plus the adjacent `tests/test_network_flow_lab.py` smoke run.
