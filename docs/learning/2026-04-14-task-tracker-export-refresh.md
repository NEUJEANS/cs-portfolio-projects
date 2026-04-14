# Python refresh for task-tracker export

Date: 2026-04-14

## Refresher
- `csv.DictWriter` is the safest standard-library path for consistent CSV headers and escaping.
- `io.StringIO` is convenient for assembling text output before optionally writing it to disk.
- Reusing existing filtering code avoids logic drift between `list` and `export`.

## Self-test
1. When should CSV be written with `newline=""` to disk?
   - When opening a real file for `csv` writing to avoid doubled blank lines on some platforms.
2. Why render into a string first?
   - It makes stdout and file output share one code path and simplifies tests.
3. What makes Markdown tables test-friendly?
   - Fixed headers and deterministic row ordering.
