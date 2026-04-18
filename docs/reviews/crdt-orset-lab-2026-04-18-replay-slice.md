# crdt-orset-lab review — replay slice

Date (UTC): 2026-04-18
Project: `projects/crdt-orset-lab`

## Pass 1 — docs / resumability review
- Reviewed the project checklist and slice notes after stabilizing the replay export path.
- Issue found: the project follow-up list still mentioned the replay/animation idea as unfinished, and there was no dedicated checklist note for the replay slice itself.
- Fix applied: updated `projects/crdt-orset-lab/CHECKLIST.md` to remove the stale replay follow-up and added `docs/checklists/2026-04-18-crdt-orset-replay-slice.md` so this run is resumable on its own.

## Pass 2 — accessibility / generated-HTML review
- Reviewed the replay page markup and the brief MDN live-region guidance against the generated page behavior.
- Issue found: the replay announcer used `aria-live="polite"` but did not mark the message as atomic, and the play/pause control did not expose pressed state.
- Fix applied: added `aria-atomic="true"` to the hidden step announcer and wired `aria-pressed` on the play button so assistive technology has a cleaner representation of replay state.

## Pass 3 — real browser smoke review
- Served `docs/artifacts/crdt-orset-lab/` through a local static HTTP server and opened `sample-ops-replay.html` in a real browser.
- Confirmed the page loaded, the slider and next-step control advanced from the initial empty cluster to step 1, the focused replica state updated, the convergence badge flipped to diverged for the first local add, and the companion artifact links rendered.
- No further issues found in the final browser pass.

## Final verification
- Re-ran `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`.
- Re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`28/28` passing after the accessibility assertions were added).
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py run-script --replicas a b c --script projects/crdt-orset-lab/sample_ops.json --timeline-markdown-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.md --timeline-mermaid-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd --timeline-svg-out docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg --timeline-html-out docs/artifacts/crdt-orset-lab/index.html --replay-html-out docs/artifacts/crdt-orset-lab/sample-ops-replay.html --json-out docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json --anti-entropy-markdown-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.md --anti-entropy-html-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.json`.
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-script --replicas a b c --script projects/crdt-orset-lab/sample_compare_ops.json --timeline-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.md --timeline-mermaid-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.mmd --timeline-svg-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.svg --timeline-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.html --replay-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-replay.html --json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-orset-snapshot.json --anti-entropy-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.md --anti-entropy-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.json --comparison-markdown-out docs/artifacts/crdt-orset-lab/lww-vs-orset.md --comparison-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset.html --comparison-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset.json`.
- Re-ran `git diff --check`.
- Opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/sample-ops-replay.html` and stepped it in a real browser.
