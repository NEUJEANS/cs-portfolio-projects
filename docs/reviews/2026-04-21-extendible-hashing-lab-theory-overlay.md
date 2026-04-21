# Extendible hashing lab review — 2026-04-21 — theory-overlay slice

## Pass 1 — theory/reference + artifact-consistency review
- Re-checked the classic linear-probing successful/miss probe formulas against Princeton/OpenDSA notes before trusting the in-progress overlay wording.
- Issue found: the theory overlay existed in JSON/Markdown/HTML outputs, but the CSV export still omitted the key theory-vs-observed fields, which made spreadsheet follow-up and artifact reuse weaker than the other formats.
- Fix: added average/peak occupied-load-factor and theory-vs-observed hit/miss columns to the CSV writer, then extended the CLI regression to assert those columns are present.

## Pass 2 — README / portfolio-story review
- Re-read the project README as if a recruiter landed on the repo without opening the dashboard first.
- Issue found: the README still treated the theory overlay as a future idea and also had a broken duplicated future-improvements line.
- Fix: added a feature bullet for the new theory overlay, removed the stale future-idea wording, and cleaned the duplicated/broken README line so the next slice starts from a sane baseline.

## Pass 3 — resumability / process review
- Reviewed the slice artifacts for whether a future run could safely resume without reconstructing why the theory overlay exists.
- Issue found: the slice had code and checklist progress, but no dedicated dated research/self-test note capturing the load-factor formulas and why occupied load factor was the right compact baseline.
- Fix: added dated research and self-test notes plus refreshed the dated slice checklist wording so the bundle is easier to resume and audit.

## Final verification
- `python3 -m py_compile projects/extendible-hashing-lab/extendible_hashing_lab.py tests/test_extendible_hashing_lab.py`
- `python3 -m unittest tests.test_extendible_hashing_lab -v` (`27/27`)
- `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py benchmark --input projects/extendible-hashing-lab/benchmark_suite.json --json-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.json --markdown-out docs/artifacts/extendible-hashing-lab/benchmark_suite_report.md --html-out docs/artifacts/extendible-hashing-lab/benchmark_suite_dashboard.html --csv-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.csv --title 'Extendible hashing vs linear probing, cuckoo hashing, and B-tree benchmark comparison'`
- repeated the benchmark export into a temp directory and verified `cmp` across JSON/Markdown/HTML/CSV outputs
- `git diff --check`
- TruffleHog secret scan passed: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
