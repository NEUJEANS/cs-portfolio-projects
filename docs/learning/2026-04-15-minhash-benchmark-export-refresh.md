# 2026-04-15 MinHash benchmark export refresh

## Quick refresh
- Keep benchmark computation separate from serialization so the same payload can feed CLI JSON, CSV summaries, and Markdown write-ups.
- For resumable CLI workflows, prefer a simple `--output` path over implicit filenames.
- Use CSV for spreadsheet/chart import and Markdown for portfolio/blog snippets.

## Self-test
1. Why keep export formatting separate from `benchmark_corpus`?
   - So the benchmark logic stays testable and deterministic while multiple output formats can reuse the same payload.
2. Why support both CSV and Markdown?
   - CSV is convenient for charts and comparison tables; Markdown is convenient for README/blog portfolio write-ups.
3. What makes the workflow resumable?
   - The benchmark can be rerun against the same corpus with an explicit output path and does not depend on hidden state.
