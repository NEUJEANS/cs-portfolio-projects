# Log Analyzer Refresh — 2026-04-14

## Quick refresh
- `re.compile(...).match(...)` is better than ad-hoc substring extraction for fixed log formats
- `Counter().most_common(n)` is enough for top-N summaries in a small CLI project
- malformed input should be counted explicitly instead of silently dropped
- offering both human text output and JSON output makes a CLI more reusable

## Self-test
1. How should missing byte counts represented as `-` be handled?
   - Convert them to `0` so totals still compute.
2. What is a useful top-level metric besides status counts?
   - Total requests, invalid lines, total bytes, average bytes, top paths, top IPs.
3. Why add JSON output?
   - So the tool can be piped into scripts or dashboards later.
