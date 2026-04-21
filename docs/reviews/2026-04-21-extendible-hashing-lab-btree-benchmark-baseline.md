# Extendible hashing lab review — 2026-04-21 — B-tree benchmark-baseline slice

## Pass 1 — CLI/report consistency review
- Re-read the benchmark CLI flow from `command_benchmark` instead of only checking the summary math.
- Issue found: `--title` only affected the Markdown report, while stdout and `--json-out` still kept the suite-file title.
- Fix: made the optional CLI title override propagate into the shared summary object before JSON/stdout/Markdown writes so all outward-facing benchmark artifacts agree.

## Pass 2 — resumability / docs review
- Reviewed the benchmark suite JSON and README as if a future reader were trying to reproduce the artifact bundle from scratch.
- Issue found: the suite file still described a cuckoo-only comparison and relied on implicit B-tree defaults, which weakened the resumable story.
- Fix: updated `projects/extendible-hashing-lab/benchmark_suite.json` to carry explicit B-tree knobs, refreshed the README/checklists to describe the B-tree baseline, and regenerated the committed benchmark artifacts.

## Pass 3 — artifact hygiene review
- Ran `git diff --check` after regenerating the CSV artifact instead of assuming the export was repo-clean.
- Issue found: the CSV writer emitted CRLF line endings, which showed up as trailing-whitespace failures in the repo diff check.
- Fix: set `csv.DictWriter(..., lineterminator='\n')` and added a regression assertion that the CLI-generated CSV text contains no `\r` characters.

## Pass 4 — regression coverage review
- Re-read the benchmark tests with the new failure modes in mind.
- Issue found: the suite had no focused regression for forced B-tree benchmark-key collisions or for the title override reaching JSON/stdout.
- Fix: added a patched collision test for `validate_benchmark_suite`, plus CLI assertions that benchmark JSON/stdout/Markdown all carry the override title.

## Pass 5 — determinism review
- Re-ran the benchmark export into a temp directory and compared JSON/Markdown/CSV outputs against the committed artifacts.
- Result: the B-tree baseline bundle stayed byte-for-byte deterministic after the CLI/doc/CSV fixes.

## Final verification
- `python3 -m py_compile projects/extendible-hashing-lab/extendible_hashing_lab.py tests/test_extendible_hashing_lab.py`
- `python3 -m unittest tests.test_extendible_hashing_lab -v` (`23/23`)
- `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py benchmark --input projects/extendible-hashing-lab/benchmark_suite.json --json-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.json --markdown-out docs/artifacts/extendible-hashing-lab/benchmark_suite_report.md --csv-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.csv --title 'Extendible hashing vs cuckoo hashing and B-tree benchmark comparison'`
- repeated the benchmark export into a temp directory and verified `cmp` across JSON/Markdown/CSV outputs
- `git diff --check`
