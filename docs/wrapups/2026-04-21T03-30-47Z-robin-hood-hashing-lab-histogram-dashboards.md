# robin-hood-hashing-lab histogram dashboards — 2026-04-21T03:30:47Z

## Sync status
- Re-checked `main`, `origin`, and `HEAD...origin/main` before editing; remote drift was still `ahead/behind 0/0`, so the unfinished local Robin Hood histogram slice was safe to resume.
- Will re-fetch again before the final push so the publish step stays safe.

## What changed
- added linear-vs-Robin-Hood benchmark Markdown and self-contained HTML artifacts under `docs/artifacts/robin-hood-hashing-lab/`
- extended the benchmark/export pipeline to carry probe-distance histograms, strategy labels, static HTML metric bars, and strategy-aware default titles/intro copy
- tightened aggregation correctness by recomputing pooled probe-distance averages/stddev from merged histogram counts instead of averaging per-trial stddevs
- preserved numeric histogram bucket ordering in CSV exports so multi-digit probe distances remain machine-readable and interview-demo friendly
- refreshed the project README/checklists plus slice-specific research/learning/review notes
- expanded regression coverage for pooled histogram stats, CSV histogram ordering, and single-strategy report rendering

## Tests and reviews run
- `python3 -m py_compile projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py tests/test_robin_hood_hashing_lab.py`
- `python3 -m unittest tests.test_robin_hood_hashing_lab -v` (`15/15`)
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --markdown-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-report.md --html-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-dashboard.html --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.csv`
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.json`
- repeated the benchmark export into temp directories and verified `cmp` across JSON/Markdown/HTML outputs
- `git diff --check`
- 4 review passes recorded in `docs/reviews/2026-04-21-robin-hood-hashing-lab-histograms.md`

## Feature commit
- `901f17c` — `feat(robin-hood-hashing-lab): add histogram benchmark dashboards`

## Next step
- add delete-heavy benchmark workloads/reports so the histogram dashboard shows how backward-shift deletion changes post-removal probe distributions
