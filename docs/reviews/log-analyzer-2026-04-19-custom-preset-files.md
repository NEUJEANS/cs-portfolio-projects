# log-analyzer review — 2026-04-19 — custom preset files

## Pass 1 — CLI/API shape
- Re-read the annotation preset expansion path and checked how a preset file would fit without creating a second rendering codepath.
- Issue found: the first draft let `--card-annotation-preset-file` appear without any `--card-annotation-preset` usage, which made the flag a confusing no-op.
- Fix: added an argparse validation error so preset files require at least one preset invocation.

## Pass 2 — validation and docs
- Re-read the custom preset loader and the README/checklist surface.
- Issue found: the draft loader accepted the feature, but the docs did not explain the JSON schema, string-step shorthand, duplicate-name guardrails, or the 4-step limit.
- Fix: added a dedicated README section, refreshed project/global checklists, and saved a short learning note documenting the schema and self-test plan.

## Pass 3 — real artifact workflow
- Re-ran the committed sample bundle under `docs/artifacts/log-analyzer/` using a checked-in preset file.
- Issue found: the committed annotated trend/comparison artifacts still reflected only built-in story labels, so the new portability win was not visible in the repo.
- Fix: added `docs/artifacts/log-analyzer/custom-card-annotation-presets.json`, regenerated the annotated SVG/HTML artifacts from that file, and spot-checked the custom labels in both trend and comparison pages.

## Final verification
- `python3 -m py_compile projects/log-analyzer/log_analyzer.py projects/log-analyzer/test_log_analyzer.py`
- `python3 -m unittest discover -s projects/log-analyzer -p 'test_*.py'`
- Real export smoke with committed artifacts:
  - trend card via `--card-annotation-preset-file docs/artifacts/log-analyzer/custom-card-annotation-presets.json --card-annotation-preset 'release-watch=2026-04-18T09:00:20Z,2026-04-18T09:01:20Z,2026-04-18T09:02:20Z'`
  - comparison card via `--card-annotation-preset-file docs/artifacts/log-analyzer/custom-card-annotation-presets.json --card-annotation-preset 'rollback-watch=2026-04-18T09:00:20Z,2026-04-18T09:01:20Z,2026-04-18T09:02:20Z'`
- `git diff --check`
