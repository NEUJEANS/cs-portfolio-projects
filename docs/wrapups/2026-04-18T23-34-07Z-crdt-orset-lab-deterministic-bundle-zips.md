# Wrap-up — 2026-04-18T23:34:07Z — crdt-orset-lab deterministic bundle ZIP rerun fix

## What changed
- safely resumed the unpublished `crdt-orset-lab` preset bundle packet slice after confirming local `main` was still ahead of `origin/main` by one clean feature commit and had no remote drift
- kept the existing portable preset bundle packet work from `340c6e2` (bundle landing pages, bundled scenario scripts, and ZIP packet links) and fixed the last publish blocker discovered during validation: rerunning `compare-presets --detail-output-dir ...` rewrote the ZIP packets even when the bundle contents were unchanged
- updated `write_bundle_zip(...)` to emit deterministic ZIP metadata (fixed timestamps, fixed permissions, stable file order) so the committed packets stay reproducible and the repo does not get spurious binary diffs on clean reruns
- extended regression coverage to assert the ZIP member timestamps and to rerun the preset generator inside the test so the bundle bytes must stay identical across unchanged reruns
- refreshed the project/docs checklist wording, self-test note, review log, README copy, and regenerated the committed preset bundle ZIP artifacts to match the deterministic writer

## Tests and reviews run
- `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`
- `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`35/35` passing)
- `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-presets --suite-markdown-out docs/artifacts/crdt-orset-lab/comparison-presets.md --suite-html-out docs/artifacts/crdt-orset-lab/comparison-presets.html --suite-json-out docs/artifacts/crdt-orset-lab/comparison-presets.json --detail-output-dir docs/artifacts/crdt-orset-lab/comparison-presets`
- reran the same `compare-presets --detail-output-dir ...` command a second time to confirm the regenerated ZIP bundle bytes stay stable when the content is unchanged
- real browser spot-checks via local `http.server`: loaded `docs/artifacts/crdt-orset-lab/comparison-presets.html` and `docs/artifacts/crdt-orset-lab/comparison-presets/concurrent-readd/index.html` to confirm the suite still exposes Bundle/ZIP links and the preset landing page still renders the portable packet entry points
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- `git diff --check`
- review log: `docs/reviews/crdt-orset-lab-2026-04-18-preset-bundle-zip-slice.md` (3 earlier passes plus the final deterministic-rerun fix noted in the verification section)

## Commit hash
- prior unpublished feature commit: `340c6e2e253811e12453e8f5588e442b90744d0d`
- deterministic rerun fix commit: `9dca1dff1a7da6d3657cc55315d018118ff8b64c`

## Next step
- add the cross-preset landing page that batch-downloads multiple preset bundle ZIP packets at once so the full OR-Set preset suite can be shared as one reviewer-friendly packet
