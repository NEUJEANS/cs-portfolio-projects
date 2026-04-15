# Review pass 1 - red-black tree CSV export

- Focus: benchmark export implementation and artifact shape
- Finding: Python CSV writer defaulted to platform-style line endings, which can add `\r\n` and make diffs/noise worse in repo-stored artifacts
- Fix: set `lineterminator="\n"` in `_benchmark_csv` so generated benchmark CSV stays stable and Unix-friendly
- Result: resolved in code and re-tested
