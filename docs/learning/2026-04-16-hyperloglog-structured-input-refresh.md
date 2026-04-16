# HyperLogLog structured-input refresh and self-test

## Refresh notes
- `csv.DictReader` is the lightest standard-library path for header-based CSV extraction and already handles quoted delimiters correctly.
- `json.loads` on each non-empty line gives a clean JSONL parser with precise line-number error reporting.
- A small dotted-path resolver is enough for nested event payloads when the project only needs deterministic local demos.
- Distinct-count ingestion should skip blank/null values and reject container values so the sketch reflects one scalar entity per record.

## Self-test
1. Why prefer `csv.DictReader` over manually splitting on commas?
   - It respects CSV quoting/escaping rules, so values containing commas do not break field extraction.
2. Why is JSONL a good fit for a resumable portfolio CLI?
   - Each line is an independent record, so partial writes/debugging stay simple and parsing errors can report the exact bad line.
3. Why reject array/object field values instead of flattening them automatically?
   - Automatic flattening muddies what one "distinct item" means; scalar-only extraction keeps the estimate easy to explain.
