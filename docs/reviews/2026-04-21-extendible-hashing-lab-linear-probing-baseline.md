# Extendible hashing lab review — 2026-04-21 — linear-probing baseline slice

## Pass 1 — regression / summary-consistency review
- Re-ran the focused unit suite after resuming the dirty local slice instead of trusting the in-progress code.
- Issue found: `summarize_benchmark_trials` now expects a `linear` section, but the synthetic inconsistency tests only modeled extendible/cuckoo/B-tree rows, causing a `KeyError` instead of the intended validation failure.
- Fix: added explicit linear metric payloads to the synthetic rows and added a dedicated regression that proves inconsistent linear metrics are rejected.

## Pass 2 — artifact export review
- Reviewed the generated benchmark artifacts and CSV writer as if a recruiter were trying to compare the baselines from exported files alone.
- Issue found: the code paths already computed linear metrics, but the CSV export still omitted them, which weakened the resumable artifact bundle.
- Fix: added linear configuration and result columns to the CSV export and extended the CLI regression to assert that `linear_average_probe_count` is present.

## Pass 3 — reproducibility / docs review
- Re-read the README, benchmark suite JSON, parser help, and dashboard copy after the code changes.
- Issue found: the suite title/config and some user-facing copy still described a cuckoo+B-tree comparison, so the repo did not fully advertise the new baseline or its tunable knobs.
- Fix: made the suite title/config explicit for linear probing, refreshed README/help/dashboard wording, updated the project checklist, and regenerated the committed benchmark artifacts.

## Pass 4 — determinism / hygiene review
- Re-exported the benchmark bundle into a temp directory and compared it byte-for-byte with the committed artifacts.
- Result: JSON/Markdown/HTML/CSV outputs stayed deterministic after the linear-baseline changes.

## Final verification
- `python3 -m py_compile projects/extendible-hashing-lab/extendible_hashing_lab.py tests/test_extendible_hashing_lab.py`
- `python3 -m unittest tests.test_extendible_hashing_lab -v` (`26/26`)
- `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py benchmark --input projects/extendible-hashing-lab/benchmark_suite.json --json-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.json --markdown-out docs/artifacts/extendible-hashing-lab/benchmark_suite_report.md --html-out docs/artifacts/extendible-hashing-lab/benchmark_suite_dashboard.html --csv-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.csv --title 'Extendible hashing vs linear probing, cuckoo hashing, and B-tree benchmark comparison'`
- repeated the benchmark export into a temp directory and verified `cmp` across JSON/Markdown/HTML/CSV outputs
- `git diff --check`
