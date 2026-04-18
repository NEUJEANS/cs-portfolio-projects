# log-analyzer review — facet comparison helpers

Date (UTC): 2026-04-18
Project: `projects/log-analyzer`

## Pass 1 — comparison output review
- Reviewed the new `facet_comparison` analysis path, text rendering, and CSV schema.
- Issue found: the first cut only made average latency deltas easy to see, which left `p95`/max latency regressions buried in JSON during release reviews.
- Fix applied: expanded the comparison summary and CSV export to include `p95` and max request/upstream latency fields and deltas for both the summary row and aligned bucket rows.

## Pass 2 — docs/checklist audit
- Reviewed README usage/docs plus the project/resumability checklists against the shipped CLI flags.
- Issue found: the resumability checklist still had a placeholder run timestamp, and the README/checklists needed explicit comparison-helper wording so the next run would not rediscover the same slice.
- Fix applied: filled in the real run timestamp, updated README feature/usage/export sections, and marked the comparison slice complete in both checklist files.

## Pass 3 — final regression + smoke audit
- Re-ran `python3 -m py_compile projects/log-analyzer/log_analyzer.py projects/log-analyzer/test_log_analyzer.py`.
- Re-ran `python3 -m unittest discover -s projects/log-analyzer -p 'test_*.py'` (`52/52` passing).
- Re-ran `git diff --check`.
- Re-ran a real temp-log smoke with `--summary-csv --time-bucket minute --facet-field env --time-bucket-facet-csv --facet-compare-field env --facet-compare-values prod staging --facet-compare-csv --format json`.
- Verified the smoke wrote summary metadata plus comparison CSV rows containing `p95_latency_ms_delta`, and no further issues were found.
