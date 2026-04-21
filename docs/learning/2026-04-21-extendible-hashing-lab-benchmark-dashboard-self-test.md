# Extendible hashing lab benchmark-dashboard self-test — 2026-04-21

## Quick refresh
- Input source for the dashboard should be the already-validated benchmark summary, not the raw suite file.
- The dashboard must stay deterministic and safe to commit, so avoid timestamps, random ordering, or browser-only dependencies.
- HTML output still needs accessibility basics: captions, column headers, and escaped dynamic text.

## Self-test
1. **Why render from the benchmark summary instead of recomputing metrics during HTML generation?**
   - So the HTML artifact stays aligned with the JSON/Markdown/CSV outputs and cannot silently diverge from the validated benchmark calculations.
2. **What needs escaping in the dashboard renderer?**
   - Title, suite source, scenario names/descriptions, metric labels, and any other dynamic strings inserted into HTML attributes or text nodes.
3. **What should the compact dashboard emphasize first?**
   - A quick scoreboard of headline tradeoff metrics, then per-scenario cards for extendible hashing, cuckoo hashing, and the B-tree page baseline.
