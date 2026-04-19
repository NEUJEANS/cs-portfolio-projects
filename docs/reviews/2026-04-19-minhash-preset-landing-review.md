# MinHash preset landing-page review log — 2026-04-19

## Pass 1 — link-path robustness audit
- reviewed whether the shared landing page would still generate correct links when the landing output directory differs from the bundle root
- issue found: the first draft used a brittle path-relativization approach around `Path.is_relative_to()` that was harder to reason about and less portable than a direct relative-path calculation
- fix: switched landing-page link generation to `os.path.relpath(...)` so JSON/Markdown/HTML links stay correct and predictable even when `output_dir` is outside the bundle subtree

## Pass 2 — CLI summary UX audit
- reviewed the new `write-preset-landing` command as a resumable automation step inside cron runs and future scripts
- issue found: the command return payload only exposed preset names/counts, so downstream automation could not quickly see the total files and total detected pairs without reopening the summary JSON file
- fix: bubbled `total_files_written` and `total_pairs_detected` into the command result, updated human-readable output, and expanded CLI/unit tests to cover the new fields

## Pass 3 — portfolio artifact completeness audit
- reviewed whether the repo actually shipped the side-by-side landing page promised by the new README/docs flow
- issue found: only the web-dev preset bundle had been checked in previously, so the landing page would not demonstrate the full mixed-language/data-science/systems/web-dev comparison story yet
- fix: generated and checked in bundle artifacts for `mixed-markdown-code-notebook`, `data-science-feature-pipeline`, and `systems-churn-reconciliation`, then regenerated the shared landing-page Markdown/HTML/JSON outputs under `docs/artifacts/minhash-near-duplicate-lab/`

## Validation rerun after fixes
- `./.venv/bin/python -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python -m pytest -q tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-preset-landing docs/artifacts/minhash-near-duplicate-lab docs/artifacts/minhash-near-duplicate-lab --json`
- `git diff --check`
