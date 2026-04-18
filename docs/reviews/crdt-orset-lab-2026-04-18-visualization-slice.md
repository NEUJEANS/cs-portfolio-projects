# crdt-orset-lab review — visualization slice

Date (UTC): 2026-04-18
Project: `projects/crdt-orset-lab`

## Pass 1 — code / renderer review
- Reviewed the new timeline renderer helpers and CLI wiring for `run-script`, `add`, `remove`, and `sync`.
- Issue found: the first draft produced a redundant title string (`OR-Set timeline — OR-Set script timeline — ...`) in the Markdown/SVG artifacts.
- Fix applied: simplified `timeline_title_from_args(...)` so exported titles stay compact (`script sample_ops.json`, etc.) while the renderers add their own context.

## Pass 2 — docs / artifact audit
- Reviewed the generated Markdown, Mermaid, and SVG artifacts against the README examples and the intended OR-Set concurrency story.
- Issue found: Markdown table rows were broken because state summaries contained literal `|` characters, which Markdown treated as extra columns.
- Fix applied: escaped pipe characters in the Markdown renderer, regenerated the committed artifacts, and rechecked the sample table output.

## Pass 3 — wording / portfolio polish review
- Reviewed the final story text, checklist/readme coherence, and final exported sample bundle for portfolio clarity.
- Issue found: the first story sentence was grammatically awkward and made the observed-remove explanation sound less crisp than the actual semantics.
- Fix applied: rewrote the sentence to `a remove tombstones only the add-tags a replica has already observed`, regenerated artifacts, and reran the validation commands.

## Post-review validation follow-up
- After the initial 3-pass review, I noticed the new timeline-output tests only exercised `run-script` even though the README promised the same export flags on single-step commands.
- Fix applied: added a dedicated CLI regression that verifies `add --timeline-*-out ...` writes Markdown, Mermaid, and SVG artifacts with the expected single-step titles/content.

## Final verification
- Re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`14/14` passing).
- Re-ran `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py`.
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py run-script --replicas a b c --script projects/crdt-orset-lab/sample_ops.json --timeline-markdown-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.md --timeline-mermaid-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd --timeline-svg-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg` and confirmed the committed artifact bundle regenerated cleanly.
- Re-ran `git diff --check`.
- No further issues found in the final pass.
