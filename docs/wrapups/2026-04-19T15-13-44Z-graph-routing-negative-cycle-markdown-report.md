# Graph routing negative-cycle lab Markdown report slice — 2026-04-19T15:13:44Z

## What changed
- safely fetched `origin`, confirmed local `main` had no remote drift, and resumed the unfinished graph-routing Markdown export slice before editing further
- added `--export-markdown` support to `graph_routing_lab.py` so the lab can emit portfolio-ready Bellman-Ford and Johnson reports as Markdown
- added `unreachable_graph.json` plus a checked-in example report at `docs/artifacts/graph-routing-negative-cycle-unreachable-report.md`
- extended the lab README and checklist coverage for the new Markdown export workflow
- expanded tests for unreachable-path handling, Markdown export content, negative-cycle report notes, CLI export flow, and Markdown cell escaping
- review fixes: escaped Markdown table cells so labels like `A|1` do not break reports, and switched the negative-cycle reachability traversal queue from `list.pop(0)` to `deque.popleft()`

## Tests and validation run
- `./.venv/bin/pytest -q tests/test_graph_routing_negative_cycle_lab.py`
- `./.venv/bin/python projects/graph-routing-negative-cycle-lab/graph_routing_lab.py projects/graph-routing-negative-cycle-lab/unreachable_graph.json --source A --export-markdown docs/artifacts/graph-routing-negative-cycle-unreachable-report.md`
- `./.venv/bin/pytest -q tests/test_network_flow_lab.py`
- `./.venv/bin/pytest -q` *(attempted broader repo smoke pass; existing unrelated collection errors remain in interval-tree/task-tracker test modules outside this slice)*
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Reviews run
- pass 1: implementation audit; fixed unescaped Markdown table cells and added regression coverage for pipe-containing labels
- pass 2: algorithm/data-shape audit; replaced the reachability helper's quadratic queue pattern with `deque` and reran focused coverage
- pass 3: smoke/docs audit; verified README commands + checked-in artifact output and recorded the unrelated full-repo pytest collection blockers
- detailed review log: `docs/reviews/2026-04-19-graph-routing-negative-cycle-markdown-report-review.md`

## Feature commit
- `562a079d29817c2f72057557d0db751309ddf535`

## Next step
- add side-by-side route-table diff reporting so students can compare graph variants and routing outcomes across multiple inputs in one artifact
