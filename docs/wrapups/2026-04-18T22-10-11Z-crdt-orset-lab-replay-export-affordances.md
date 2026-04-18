# Wrap-up — 2026-04-18T22:10:11Z — crdt-orset-lab replay export-affordances slice

## What changed
- added replay-page actions for copying the exact frame URL, copying the stable sync-checkpoint URL, and downloading the current checkpoint as a standalone SVG card
- generated richer in-browser checkpoint SVG exports that summarize the step, replica states, anti-entropy transfer details, and deep links for the chosen checkpoint
- regenerated the committed baseline and comparison replay artifacts so the new actions are available in the checked-in portfolio bundle
- documented the slice with checklist, research, self-test, and review notes, and cleaned duplicated future-follow-up bullets in the project docs
- fixed two embedded-JavaScript issues found during review (Python escape handling for the regex literal and newline escaping in the generated SVG export code)
- added a regression test that extracts the generated replay script and runs `node --check` so future generated-JS syntax mistakes are caught automatically

## Tests and reviews run
- `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`
- `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (29/29 passing)
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py run-script --replicas a b c --script projects/crdt-orset-lab/sample_ops.json --timeline-html-out docs/artifacts/crdt-orset-lab/index.html --replay-html-out docs/artifacts/crdt-orset-lab/sample-ops-replay.html --json-out docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json --anti-entropy-html-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.json`
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-script --replicas a b c --script projects/crdt-orset-lab/sample_compare_ops.json --timeline-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.html --replay-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-replay.html --json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-orset-snapshot.json --anti-entropy-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.html --anti-entropy-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.json --comparison-html-out docs/artifacts/crdt-orset-lab/lww-vs-orset.html --comparison-json-out docs/artifacts/crdt-orset-lab/lww-vs-orset.json`
- `node --check` against the extracted generated replay script during the new regression test
- `git diff --check`
- secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (0 verified, 0 unverified)
- review log: `docs/reviews/crdt-orset-lab-2026-04-18-replay-export-affordances-slice.md` (3 passes: generated-script/code review, docs/artifact consistency, real browser smoke)
- browser smoke: served the repo locally, opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/sample-ops-replay.html?v=3#sync-2`, confirmed it lands on step 5, verified the copy-sync action note, and verified the SVG-download action note

## Commit hash
- feature commit: `4b4647d0257a0ca65d97ed85a5289c41f00b331f`

## Next step
- add PNG/export bundling on top of the replay checkpoint SVG downloads so slide decks can grab bitmap assets without leaving the replay page
