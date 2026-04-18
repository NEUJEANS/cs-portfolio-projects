# crdt-orset-lab review — OR-Set vs LWW comparison slice

Date (UTC): 2026-04-18
Project: `projects/crdt-orset-lab`

## Pass 1 — implementation wiring review
- Reviewed the pre-existing local comparison diff in `crdt_orset_lab.py`.
- Issue found: the new LWW/comparison helpers were present but unreachable because the CLI had no `compare-script` parser path, and the Markdown renderer still contained escaped-string syntax that broke imports.
- Fix applied: repaired the Markdown escaping, added a timeline-length guard, introduced a real `compare-script` subcommand, and wired the comparison outputs through `main(...)`.

## Pass 2 — scenario / semantics review
- Reviewed whether the scenario actually demonstrated a semantic difference instead of just duplicating the baseline OR-Set sample.
- Issue found: the original baseline `sample_ops.json` leaves the element present in both models, so it is not a strong comparison artifact by itself.
- Fix applied: added `sample_compare_ops.json` with explicit logical timestamps so the OR-Set keeps `notebook` while the LWW-element-set drops it after the later remove timestamp.

## Pass 3 — docs / artifact / regression review
- Reviewed README usage, checklist state, committed artifact names, and test coverage after the implementation stabilized.
- Issue found: without explicit docs/tests for `compare-script`, the slice would be hard to resume and easy to regress later.
- Fix applied: updated README + project checklist, added comparison-focused unit/CLI tests, generated the committed comparison artifact bundle, and added dedicated research/learning notes for resumability.

## Final verification
- Re-ran `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`.
- Re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`20/20` passing).
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-script --replicas a b c --script projects/crdt-orset-lab/sample_compare_ops.json --timeline-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.md --timeline-mermaid-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.mmd --timeline-svg-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.svg --timeline-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.html --json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-orset-snapshot.json --comparison-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset.md --comparison-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset.html --comparison-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset.json`.
- Re-ran `git diff --check`.
- No further issues found in the final pass.
