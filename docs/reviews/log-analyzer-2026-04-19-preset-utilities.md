# log-analyzer review — 2026-04-19 — preset utilities

## Pass 1 — utility-mode CLI contract
- Re-read the parser/main flow to make sure the new preset helper flags do not fork the export pipeline or weaken existing validation.
- Issue found: the first draft only covered basic list/preview success paths, so the combined JSON payload shape (`--list-card-annotation-presets` + `--preview-card-annotation-preset`) could regress unnoticed.
- Fix: added CLI regression coverage for the combined JSON utility payload plus custom-file preview expansion.

## Pass 2 — docs/discoverability
- Re-read the README quick-start commands and the custom preset section from the perspective of a student skimming for demo-ready workflows.
- Issue found: the new helper flags existed in code, but the README still forced readers to infer the no-logfile workflow and did not point to any committed sample outputs.
- Fix: added no-logfile examples, documented the helper workflow explicitly, and linked the committed sample catalog/preview artifacts.

## Pass 3 — committed artifact/resumability check
- Re-ran the helper commands against the committed sample preset file under `docs/artifacts/log-analyzer/`.
- Issue found: the repo contained the sample preset JSON, but no generated catalog/preview outputs that prove the helper mode or make future README screenshots easier.
- Fix: committed `card-annotation-preset-catalog.txt` and `card-annotation-preset-preview.json` generated from the sample preset file.

## Final verification
- `python3 -m py_compile projects/log-analyzer/log_analyzer.py`
- `python3 -m unittest discover -s projects/log-analyzer -p 'test_*.py'`
- Real helper smokes:
  - `python3 projects/log-analyzer/log_analyzer.py --list-card-annotation-presets`
  - `python3 projects/log-analyzer/log_analyzer.py --format json --preview-card-annotation-preset 'deploy-rollback-recovery=2026-04-18T09:00:20Z,2026-04-18T09:01:40Z,2026-04-18T09:03:10Z'`
  - `python3 projects/log-analyzer/log_analyzer.py --list-card-annotation-presets --preview-card-annotation-preset 'release-watch=2026-04-18T09:00:20Z,2026-04-18T09:01:40Z,2026-04-18T09:03:10Z' --card-annotation-preset-file docs/artifacts/log-analyzer/custom-card-annotation-presets.json`
- Real export regression smoke with the same sample preset file:
  - `python3 projects/log-analyzer/log_analyzer.py docs/artifacts/log-analyzer/release-comparison-sample.log --time-bucket minute --time-bucket-card-svg /tmp/log-analyzer-trend-card.svg --time-bucket-card-html /tmp/log-analyzer-trend-card.html --card-annotation-preset-file docs/artifacts/log-analyzer/custom-card-annotation-presets.json --card-annotation-preset 'release-watch=2026-04-18T09:00:20Z,2026-04-18T09:01:20Z,2026-04-18T09:02:20Z'`
  - `python3 projects/log-analyzer/log_analyzer.py docs/artifacts/log-analyzer/release-comparison-sample.log --time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-card-svg /tmp/log-analyzer-compare-card.svg --facet-compare-card-html /tmp/log-analyzer-compare-card.html --card-annotation-preset-file docs/artifacts/log-analyzer/custom-card-annotation-presets.json --card-annotation-preset 'rollback-watch=2026-04-18T09:00:20Z,2026-04-18T09:01:20Z,2026-04-18T09:02:20Z'`
- `git diff --check`
