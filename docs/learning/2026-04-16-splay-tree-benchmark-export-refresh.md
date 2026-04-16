# 2026-04-16 splay-tree benchmark export refresh

Refresh points:
- `csv.DictWriter` keeps CLI-generated tabular output stable by locking column order instead of depending on dict insertion side effects.
- Benchmark JSON should stay identical to stdout so exported artifacts and terminal output cannot drift.
- File-output helpers should create parent directories before writing so artifact commands remain resumable.

Self-test:
1. Why prefer a fixed CSV header for benchmark exports?
   Because spreadsheet/chart workflows depend on stable column names and order across repeated runs.
2. Why write the same payload to stdout and optional JSON output?
   So docs, tests, and generated artifacts all describe one canonical benchmark result shape.
3. Why should the export command create parent directories automatically?
   Because portfolio artifact paths often point into fresh `artifacts/` or `docs/artifacts/` folders during clean runs.
