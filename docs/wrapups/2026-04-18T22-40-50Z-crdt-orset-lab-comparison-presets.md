# Wrap-up — 2026-04-18T22:40:50Z — crdt-orset-lab comparison preset-suite slice

## What changed
- safely resumed the dirty local `crdt-orset-lab` preset-suite slice after confirming tracked `main` still matched `origin/main` (`ahead/behind 0/0` before editing)
- added a built-in comparison preset registry plus `list-presets` and `compare-presets` CLI flows so the project can summarize multiple OR-Set vs LWW scenarios with one command
- added two committed preset scripts (`presets/unobserved-remove.json` and `presets/observed-remove-sync.json`) alongside the existing `sample_compare_ops.json` divergence story
- generated and committed portfolio-ready preset-suite artifacts at `docs/artifacts/crdt-orset-lab/comparison-presets.{md,html,json}`
- refreshed the README, project/docs checklists, research note, self-test note, and review log for resumable follow-through
- fixed one review-found CLI ergonomics issue so an unknown preset name now surfaces as a concise parser error instead of a raw Python traceback

## Tests and reviews run
- `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`
- `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`35/35` passing)
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py list-presets --json`
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-presets --suite-markdown-out docs/artifacts/crdt-orset-lab/comparison-presets.md --suite-html-out docs/artifacts/crdt-orset-lab/comparison-presets.html --suite-json-out docs/artifacts/crdt-orset-lab/comparison-presets.json`
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-presets --preset missing` (verified concise parser error without traceback)
- `git diff --check`
- review log: `docs/reviews/crdt-orset-lab-2026-04-18-comparison-presets-slice.md` (3 passes: code/CLI ergonomics, docs/artifact consistency, real browser spot-check)
- browser spot-check: served the repo locally and opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/comparison-presets.html`, then confirmed the gallery renders 3 scenario cards plus the `2 divergent / 1 aligned` summary

## Commit hash
- feature commit: `bc8207e10ba24f8af076e7d33d1c72325a799595`

## Next step
- add per-preset detail export bundles so each summary card can link straight to its own timeline, replay, and anti-entropy pages
