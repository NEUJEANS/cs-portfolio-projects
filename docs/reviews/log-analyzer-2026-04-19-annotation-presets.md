# log-analyzer review — 2026-04-19 — annotation presets

## Pass 1 — CLI/API shape
- Checked whether the new preset helper stayed narrow and composable with the existing card export flow.
- Issue found: the first draft only added code/tests; the README and resumability checklists did not document `--card-annotation-preset` yet.
- Fix: updated `projects/log-analyzer/README.md`, `projects/log-analyzer/CHECKLIST.md`, and `docs/checklists/log-analyzer.md` with preset examples, slice status, and next-step notes.

## Pass 2 — validation and regression coverage
- Re-read the preset expansion path and CLI handling around `main(...)`.
- Issue found: preset expansion/normalization errors would bubble out as raw Python exceptions instead of the existing argparse-style CLI failure path.
- Fix: wrapped preset expansion + annotation normalization in `parser.error(...)` handling and added coverage for preset expansion, successful CLI preset exports, missing-card validation, and wrong-timestamp-count validation.

## Pass 3 — real artifact workflow
- Re-ran the project against the committed sample log bundle under `docs/artifacts/log-analyzer/`.
- Issue found: the sample bundle still reflected hand-written annotation commands, so the new ergonomics were not exercised by the committed artifacts.
- Fix: regenerated the annotated trend/comparison HTML+SVG bundle (and comparison CSV companion) using the preset-powered commands, then rechecked `git diff --check`.

## Final verification
- `python3 -m py_compile projects/log-analyzer/log_analyzer.py projects/log-analyzer/test_log_analyzer.py`
- `python3 -m unittest discover -s projects/log-analyzer -p 'test_*.py'`
- Real preset export smoke for:
  - `--time-bucket-card-svg` / `--time-bucket-card-html` with `deploy-incident-recovery`
  - `--facet-compare-card-svg` / `--facet-compare-card-html` / `--facet-compare-csv` with `deploy-rollback-recovery`
- `git diff --check`
