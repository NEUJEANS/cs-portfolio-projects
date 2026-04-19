# Graph routing negative-cycle lab route diff review — 2026-04-19

## Pass 1 — artifact/readability audit
- Reviewed the new comparison summaries in pretty output and the Markdown artifact.
- Issue found: the summary used `->` both inside route paths and between the old/new path values, so strings like `A -> C -> B -> A -> B` were ambiguous in the checked-in report.
- Fix applied: changed path summaries to explicit bracketed transitions like `path: [A -> C -> B] => [A -> B]`.
- Validation: reran the focused test suite and regenerated `docs/artifacts/graph-routing-negative-cycle-route-diff-report.md`.

## Pass 2 — edge-case coverage audit
- Reviewed how the comparison behaves when graph variants do not have exactly the same node set.
- Issue found: the implementation already handled node additions/removals via `presence`, but there was no direct regression test proving that behavior.
- Fix applied: added `test_compare_reports_marks_presence_changes_when_candidate_adds_node`.
- Validation: confirmed the comparison reports a `presence` change with `node added in candidate graph`.

## Pass 3 — CLI/guardrail audit
- Reviewed the new CLI surface for compare-only export flows.
- Issue found: `--export-compare-markdown` had runtime validation, but no dedicated regression test covered the failure path when `--compare-graph` is omitted.
- Fix applied: added `test_cli_compare_markdown_requires_compare_graph`.
- Validation: reran the focused test suite, JSON compare smoke, Markdown export smoke, and `git diff --check`; all passed.
