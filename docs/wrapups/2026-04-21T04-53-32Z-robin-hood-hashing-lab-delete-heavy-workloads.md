# robin-hood-hashing-lab delete-heavy workloads — 2026-04-21T04:53:32Z

## Sync status
- Re-checked `main`, `origin`, and `HEAD...origin/main` before resuming the dirty local Robin Hood slice; remote drift was `ahead/behind 0/0`.
- Fetched `origin` again right before publish prep; drift was still `0/0`, so the final push remained safe.

## What changed
- added workload-aware benchmarking with `fill-only` and `delete-heavy` modes, configurable delete fractions, delete probe metrics, and effective post-workload load factors
- extended both Robin Hood and linear-probing tables with deletion metrics so post-removal comparisons stay apples-to-apples
- regenerated committed CSV/JSON/Markdown/HTML artifact bundles for the new delete-heavy benchmark story
- added regression coverage for workload parsing, delete-count calculation, wrapped linear-probing deletion behavior, summary aggregation, and CLI exports
- tightened the report/dashboard wording so requested load factors are clearly distinguished from rounded effective fill levels
- updated the project README, main checklist, slice checklist, and review notes so the slice is resumable

## Tests and reviews run
- brief external research: Code Capsule note on backward-shift deletion and stable post-delete DIB variance
- `python3 -m py_compile projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py tests/test_robin_hood_hashing_lab.py`
- `python3 -m unittest tests.test_robin_hood_hashing_lab -v` (`18/18`)
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --workloads fill-only,delete-heavy --delete-fraction 0.3 --markdown-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-report.md --html-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-dashboard.html --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.csv`
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --workloads fill-only,delete-heavy --delete-fraction 0.3 --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.json`
- repeated the benchmark export into separate temp directories and verified `cmp` across Markdown/HTML/CSV/JSON outputs
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (clean: 0 verified, 0 unknown)
- 4 review passes recorded in `docs/reviews/2026-04-21-robin-hood-hashing-lab-delete-heavy.md`

## Feature commit
- `0098064` — `feat(robin-hood-hashing-lab): add delete-heavy benchmark workloads`

## Next step
- add unsuccessful-lookup benchmark workloads/histograms so misses become part of the interview story too
