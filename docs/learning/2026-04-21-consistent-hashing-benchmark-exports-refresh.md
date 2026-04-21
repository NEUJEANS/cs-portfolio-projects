# 2026-04-21 Consistent Hashing Benchmark Export Refresh

## Refresher
- Benchmark exports should be derived from the measured payload, not recomputed separately, so the artifact and stdout JSON always agree.
- CSV should stay flat and repetitive on purpose because spreadsheet/chart tools prefer one row per benchmark point.
- A Markdown export is most useful when it highlights the best tested configuration and keeps the table small enough to skim quickly.

## Quick self-test
1. Why keep JSON stdout even after adding CSV and Markdown outputs? So the CLI stays scriptable and test-friendly.
2. Why repeat benchmark metadata in every CSV row? So each row is self-describing when imported into spreadsheets or filtered in notebooks.
3. Why summarize the best imbalance point in Markdown? Because portfolio readers usually want the conclusion before the raw series.
