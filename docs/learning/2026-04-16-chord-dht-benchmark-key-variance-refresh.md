# Chord DHT benchmark key variance refresh

- Timestamp: 2026-04-16 04:41 UTC
- Why this slice: the README still listed per-key variance summaries as the next meaningful benchmark-reporting gap after sample-comparison export.
- Refresh notes:
  - Aggregating per-key variance can reuse the existing sample-comparison payload because each seeded sample already stores full benchmark cases.
  - A useful portfolio summary should track average hops, hop-savings spread, and which seed/start-node combinations produce the best and worst savings for each key.
  - Keeping Markdown and CSV outputs aligned makes it easy to reuse the same analysis in README snippets, charts, and spreadsheets.
- Self-test:
  - `python3 - <<'PY'`
    `cases = [{'key': 'compiler', 'hop_savings': 2}, {'key': 'compiler', 'hop_savings': 0}]`
    `print(max(item['hop_savings'] for item in cases) - min(item['hop_savings'] for item in cases))`
    `PY`
