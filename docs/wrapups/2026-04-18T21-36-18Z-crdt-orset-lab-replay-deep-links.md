# Wrap-up — 2026-04-18T21:36:18Z — crdt-orset-lab replay deep-links slice

## What changed
- added hash-based replay routing so generated OR-Set replay pages can open directly on exact frames like `#step-3` or stable sync checkpoints like `#sync-2`
- numbered sync checkpoints in the replay-frame model and kept the browser state synchronized with `history.replaceState(...)` plus `hashchange` handling
- surfaced a deep-link panel inside the replay UI with the canonical hash, exact frame URL, stable sync checkpoint URL, and the full sync checkpoint list
- fixed a browser-review UX issue so sync frames now expose both the precise `#step-N` link and the stable `#sync-N` link instead of duplicating the same checkpoint URL twice
- regenerated the committed baseline and comparison replay artifacts and updated README/checklist/research/self-test/review docs for resumable follow-up

## Tests and reviews run
- `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`
- `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (28/28 passing; re-run after the browser-review fix)
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py run-script --replicas a b c --script projects/crdt-orset-lab/sample_ops.json --timeline-html-out docs/artifacts/crdt-orset-lab/index.html --replay-html-out docs/artifacts/crdt-orset-lab/sample-ops-replay.html --json-out docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json --anti-entropy-html-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.json`
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-script --replicas a b c --script projects/crdt-orset-lab/sample_compare_ops.json --timeline-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.html --replay-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-replay.html --json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-orset-snapshot.json --anti-entropy-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.json --comparison-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset.html --comparison-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset.json`
- `git diff --check`
- secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (0 verified, 0 unverified)
- review log: `docs/reviews/crdt-orset-lab-2026-04-18-replay-deep-links-slice.md` (3 passes: hash/deep-link wiring, docs/artifact consistency, real browser smoke + post-fix re-open)
- browser smoke: served the repo locally and opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/sample-ops-replay.html#sync-2`, then verified the page lands on step 5 and exposes both `#step-5` and `#sync-2`

## Commit hash
- feature commit: `4dfdf990bddb38bfca7402c8946b78fb051eb5d5`

## Next step
- add copy-link or image-export affordances from replay checkpoints so slide decks can capture a chosen CRDT state even faster
