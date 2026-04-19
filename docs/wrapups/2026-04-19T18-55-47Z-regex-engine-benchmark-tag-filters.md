# Regex engine benchmark tag-filter wrap-up

- timestamp: `2026-04-19T18:55:47Z`
- project: `regex-engine-lab`
- feature commit: `a9c2c13` (`feat(regex-engine-lab): add benchmark suite tag filters`)
- sync status before edits: `main` vs `origin/main` was `ahead/behind 0/0` after `git fetch origin`

## What changed
- added optional per-case benchmark `tags` metadata to the regex engine’s built-in sample suite and JSON-backed suite-file contract
- added repeatable `benchmark --include-tag` / `--exclude-tag` filters for built-in and file-backed suites, with lowercase/trim normalization plus readable validation errors for overlap or empty selections
- surfaced suite tags and applied-filter metadata in the JSON/Markdown benchmark reports so filtered runs stay self-describing
- refreshed the committed benchmark suite JSON plus generated sample-suite, full portfolio-workload, and smaller interview-demo benchmark artifacts under `docs/artifacts/regex-engine-lab/`
- added a dedicated `projects/regex-engine-lab/CHECKLIST.md` plus research/learning/review notes so the project is easier to resume on later cron runs

## Tests and review
- `python3 -m py_compile projects/regex-engine-lab/regex_engine_lab.py projects/regex-engine-lab/test_regex_engine_lab.py`
- `python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py'` → `36 tests`, `OK`
- `python3 projects/regex-engine-lab/regex_engine_lab.py benchmark --sample-suite --iterations 50 --warmup 5 --json-out docs/artifacts/regex-engine-lab/benchmark-sample-suite.json --markdown-out docs/artifacts/regex-engine-lab/benchmark-sample-suite.md`
- `python3 projects/regex-engine-lab/regex_engine_lab.py benchmark --suite-file docs/examples/regex-engine-benchmark-suite.json --iterations 50 --warmup 5 --json-out docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.json --markdown-out docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.md`
- `python3 projects/regex-engine-lab/regex_engine_lab.py benchmark --suite-file docs/examples/regex-engine-benchmark-suite.json --label interview-demo --include-tag interview-demo --iterations 50 --warmup 5 --json-out docs/artifacts/regex-engine-lab/benchmark-interview-demo.json --markdown-out docs/artifacts/regex-engine-lab/benchmark-interview-demo.md`
- filter smoke: `python3 projects/regex-engine-lab/regex_engine_lab.py benchmark --suite-file docs/examples/regex-engine-benchmark-suite.json --include-tag interview-demo --exclude-tag shorthand --iterations 1 --warmup 0`
- empty-selection failure smoke: `python3 projects/regex-engine-lab/regex_engine_lab.py benchmark --suite-file docs/examples/regex-engine-benchmark-suite.json --include-tag not-a-real-tag --iterations 1 --warmup 0` → exit `2`
- `git diff --check`
- review passes logged in `docs/reviews/2026-04-19-regex-engine-benchmark-tag-filters-review.md`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` → clean

## Next step
- render the tagged benchmark suites into a small HTML summary card or comparison dashboard so interview-demo and portfolio-batch subsets are easier to show visually
