# Wrap-up — 2026-04-18T23:07:00Z — crdt-orset-lab preset detail-bundle slice

## What changed
- safely resumed the dirty local `crdt-orset-lab` preset-detail slice after confirming tracked `main` still matched `origin/main` (`ahead/behind 0/0` before the new commit)
- extended `compare-presets` with `--detail-output-dir` so one command can emit a suite summary plus a full per-preset artifact bundle
- added reusable relative-path helpers and `detail_bundle` metadata so suite Markdown/HTML/JSON outputs can link directly to each preset's comparison page, timeline page, replay page, anti-entropy report, and raw snapshot
- generated and committed per-preset detail bundles under `docs/artifacts/crdt-orset-lab/comparison-presets/` for `concurrent-readd`, `unobserved-remove`, and `observed-remove-sync`
- refreshed the README, project/docs checklists, research note, self-test note, and review log so the slice stays resumable
- fixed one review-found documentation gap: the README now documents `--detail-output-dir` and points at real committed detail-bundle artifacts instead of only the top-level suite summary

## Tests and reviews run
- `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`
- `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`35/35` passing)
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-presets --suite-markdown-out docs/artifacts/crdt-orset-lab/comparison-presets.md --suite-html-out docs/artifacts/crdt-orset-lab/comparison-presets.html --suite-json-out docs/artifacts/crdt-orset-lab/comparison-presets.json --detail-output-dir docs/artifacts/crdt-orset-lab/comparison-presets`
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py list-presets --json`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- `git diff --check`
- review log: `docs/reviews/crdt-orset-lab-2026-04-18-preset-detail-bundles-slice.md` (3 passes: code/relative-link wiring, docs/artifact consistency, real browser spot-check)
- browser spot-check: served the repo locally and opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/comparison-presets.html`, then followed the `Comparison` link for `concurrent-readd` to confirm relative navigation into the detail bundle works in a real browser

## Commit hash
- feature commit: `2d12921e8b993a2a7e59db8dfa27db24d8a31967`

## Next step
- add a tiny landing/index page or portable zip export inside each preset detail bundle so a single scenario can be shared as one self-contained packet
