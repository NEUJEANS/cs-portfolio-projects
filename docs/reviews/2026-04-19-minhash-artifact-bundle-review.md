# MinHash artifact bundle review log — 2026-04-19

## Pass 1 — bundle isolation audit
- reviewed whether artifact bundles stayed faithful to the preset files generated in the current run
- issue found: `build_preset_artifact_bundle()` re-scanned the whole destination directory, so a reused destination with extra matching files could contaminate the reported pair counts and screenshots
- fix: restricted bundle analysis to the files written for the current preset run, filtered through the preset glob so the bundle stays deterministic and resumable even when the destination folder already contains unrelated files

## Pass 2 — notebook preview robustness audit
- reviewed preview extraction for mixed-language presets that include notebooks
- issue found: the notebook preview helper only handled list-based cell sources, but some notebook JSON serializers emit `source` as a single string
- fix: taught `_preview_text_for_bundle()` to accept both string and list cell sources so notebook cards stay readable across serializer variations

## Pass 3 — docs / operator-UX audit
- reviewed the README flow from feature discovery to CLI usage
- issue found: the artifact-bundle example only showed the web-dev preset and could be read as a one-off path rather than a flag supported by every curated preset
- fix: clarified in the README that `--artifact-bundle-dir` works for the mixed-markdown, data-science, and systems presets as well

## Validation rerun after fixes
- `./.venv/bin/python -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python -m pytest -q tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-preset web-dev-component-clones docs/artifacts/minhash-near-duplicate-lab/web-dev-component-clones/preset --artifact-bundle-dir docs/artifacts/minhash-near-duplicate-lab/web-dev-component-clones/bundle --json`
- `git diff --check`
