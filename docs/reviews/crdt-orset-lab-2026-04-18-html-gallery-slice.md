# crdt-orset-lab review — HTML gallery slice

Date (UTC): 2026-04-18
Project: `projects/crdt-orset-lab`

## Pass 1 — correctness / state-summary review
- Reviewed the new HTML gallery summary against both converged and non-converged snapshots.
- Issue found: the first draft summarized membership/tombstones from only the first replica, which was misleading for single-step `add` / `remove` / `sync` flows before convergence.
- Fix applied: the HTML summary now shows shared values only when every replica agrees; otherwise it explicitly says `mixed by replica`, and a new regression test covers the non-converged case.

## Pass 2 — artifact-navigation review
- Reviewed whether the browser page exposed the full reproducible bundle instead of only the polished outputs.
- Issue found: the first gallery version linked Markdown / Mermaid / SVG / JSON outputs, but not the source scenario script that actually generated the run.
- Fix applied: `run-script` galleries now include a relative `Scenario script` link back to `sample_ops.json`, so the bundle is reproducible from a single landing page.

## Pass 3 — docs / resumability review
- Reviewed README, checklist state, research note, learning/self-test note, and the committed artifact directory for slice drift.
- Issue found: after the implementation stabilized, the checklist still described the gallery work as unfinished and the follow-up list still included the already-shipped gallery idea.
- Fix applied: updated the checklist to mark the HTML/JSON slice complete, expanded the quality-check bullets to mention the new export paths, and replaced the stale follow-up with the next stronger comparison-page idea.

## Final verification
- Re-ran `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`.
- Re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`16/16` passing).
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py run-script --replicas a b c --script projects/crdt-orset-lab/sample_ops.json --timeline-markdown-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.md --timeline-mermaid-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd --timeline-svg-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg --timeline-html-out docs/artifacts/crdt-orset-lab/index.html --json-out docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json` and confirmed the committed bundle regenerated cleanly.
- Re-ran `git diff --check`.
- No further issues found in the final pass.
