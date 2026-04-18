# crdt-orset-lab learning/self-test — 2026-04-18 — replay-controls slice

## Refresh
Only a short refresh was needed: generated HTML can stay demo-ready if it leans on native controls (`button`, `input[type=range]`, `select`) and computes any navigation helpers directly from the exported timeline data.

## Self-test checklist
- re-ran `python3 -m py_compile` on both `crdt_orset_lab.py` and `test_crdt_orset_lab.py`
- re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` after adding the replay controls and render assertions
- regenerated the committed replay artifacts from the CLI instead of editing exported HTML by hand
- served the repo locally and opened `docs/artifacts/crdt-orset-lab/sample-ops-replay.html` in a real browser
- verified `Next sync` jumped from the initial frame to step 2 (`a ↔ b sync (both)`)
- switched playback speed to the fastest preset and confirmed the replay advanced in the browser before pausing it

## Takeaway
For portfolio artifacts, the strongest replay controls are the ones that stay data-driven. If the controls can be regenerated from the same CLI snapshot as the rest of the artifacts, the demo stays reproducible and cheap to maintain.
