# crdt-orset-lab review — anti-entropy slice

Date (UTC): 2026-04-18
Project: `projects/crdt-orset-lab`

## Pass 1 — data-model review
- Reviewed the new digest/payload summary helpers to make sure the anti-entropy numbers were derived from deterministic state, not ad-hoc string formatting.
- Issue found: `active_element_count` filtered elements through `str(element)`, which would undercount valid falsy values such as `""` or `0` if a scenario ever used them.
- Fix applied: changed the count to use the real iterable length instead of truthiness-by-string conversion.

## Pass 2 — renderer review
- Reviewed the Markdown/HTML anti-entropy reports for edge cases instead of only the happy-path sample with several sync events.
- Issue found: the HTML renderer had a no-sync placeholder row, but the Markdown renderer emitted only the table header with no explanatory row.
- Fix applied: added a matching Markdown placeholder row for runs that have no sync steps yet, and added a regression test for that case.

## Pass 3 — docs / regression / artifact review
- Reviewed README usage, artifact-link wiring, and CLI regression coverage after the anti-entropy outputs were working.
- Issue found: the new export paths were easy to regress because there was no dedicated coverage for run-script artifact generation plus comparison-page anti-entropy links.
- Fix applied: added targeted CLI tests for anti-entropy Markdown/HTML/JSON exports, added comparison-link coverage, regenerated the committed artifact bundles, and updated README examples to include the new outputs.

## Final verification
- Re-ran `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`.
- Re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`25/25` passing).
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py run-script --replicas a b c --script projects/crdt-orset-lab/sample_ops.json --timeline-markdown-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.md --timeline-mermaid-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd --timeline-svg-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg --timeline-html-out docs/artifacts/crdt-orset-lab/index.html --json-out docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json --anti-entropy-markdown-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.md --anti-entropy-html-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.json`.
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-script --replicas a b c --script projects/crdt-orset-lab/sample_compare_ops.json --timeline-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.md --timeline-mermaid-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.mmd --timeline-svg-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.svg --timeline-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.html --json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-orset-snapshot.json --anti-entropy-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.md --anti-entropy-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.json --comparison-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset.md --comparison-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset.html --comparison-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset.json`.
- Re-ran `git diff --check`.
- No further issues found in the final pass.
