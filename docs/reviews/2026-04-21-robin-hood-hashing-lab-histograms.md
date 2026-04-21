# Robin Hood hashing lab review — 2026-04-21 — histogram/report slice

## Pass 1 — pooled histogram math review
- Re-read the summary path from `run_benchmark(...)` into `summarize_benchmark(...)` instead of only eyeballing the rendered report.
- Issue found: the aggregate report was averaging per-trial probe-distance standard deviations, which is not the same as the pooled stddev of the merged histogram shown in the report.
- Fix: merged histogram counts first, recomputed pooled average probe distance + stddev from those counts, and added a regression test that locks the pooled-stddev math.

## Pass 2 — machine-readable export review
- Audited the CSV benchmark writer with multi-digit probe distances in mind instead of only the current sample artifact.
- Issue found: `json.dumps(..., sort_keys=True)` reordered stringified histogram keys lexicographically, so future buckets like `10` would sort before `2` in the CSV cell.
- Fix: preserved the already numeric-sorted insertion order when serializing histogram JSON and added a regression test that checks the CSV cell stays `0, 2, 10` instead of `0, 10, 2`.

## Pass 3 — single-strategy copy review
- Re-read the benchmark title/intro flow as if a student ran `--strategies robin-hood` without the linear baseline.
- Issue found: the default title and hero copy still said "comparison" / "against a linear-probing baseline" even when only one strategy was selected.
- Fix: added a strategy-aware default title + intro helper and regression coverage for single-strategy Markdown/HTML outputs.

## Pass 4 — artifact determinism review
- Re-ran the benchmark export twice into temp directories after the math/CSV/title fixes.
- Result: JSON/Markdown/HTML outputs stayed byte-for-byte deterministic across repeated runs with the same seed.

## Final verification
- `python3 -m py_compile projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py tests/test_robin_hood_hashing_lab.py`
- `python3 -m unittest tests.test_robin_hood_hashing_lab -v` (`15/15`)
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --markdown-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-report.md --html-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-dashboard.html --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.csv`
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.json`
- repeated the benchmark export into temp directories and verified `cmp` across JSON/Markdown/HTML outputs
- `git diff --check`
