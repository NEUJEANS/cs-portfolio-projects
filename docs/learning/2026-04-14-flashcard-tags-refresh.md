# Flashcard Quiz App Refresh — 2026-04-14

## Quick refresh
- `csv.DictReader` safely handles optional columns as long as required headers are validated.
- Repeating an argparse option with `action='append'` is a clean way to support multi-tag filters.
- Normalize user-facing taxonomy data (tags) early to avoid mismatched casing and duplicate values.
- For compact analytics, count missed-card tags during quiz execution and summarize afterward.

## Self-test
1. Why parse tags during load instead of during filtering?
   - So card objects carry normalized metadata once, reducing repeated parsing and keeping filters/tests simpler.
2. Why require all requested tags instead of any requested tag?
   - It makes focused study sessions deterministic and useful for intersecting topics like `graphs` + `algorithms`.
3. Why report weakest tags from incorrect answers?
   - It gives a portfolio-friendly feedback loop without adding persistent storage yet.
