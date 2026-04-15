# Mini MapReduce dataset-family discovery review — pass 3

- Scope reviewed: CLI failure mode for unsupported plugin dataset families.
- Checks: ran `benchmark --dataset-family hackathon` against `plugins_average_score.py`.
- Issue found: the CLI returned a Python traceback instead of a clean argparse-style error.
- Fix applied: wrapped `execute_job()` and `benchmark_job()` calls in `main()` so `ValueError` becomes `parser.error(...)`.
- Re-test: confirmed non-zero exit with a clean message and no traceback.
