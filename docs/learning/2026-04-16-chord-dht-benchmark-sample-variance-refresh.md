# Chord DHT benchmark sample variance refresh

- Timestamp: 2026-04-16 04:11 UTC
- Why this slice: the README still listed benchmark variance across random start-node subsets as the next meaningful portfolio gap.
- Refresh notes:
  - `random.Random(seed).sample(...)` gives deterministic, duplicate-free start-node subsets for repeatable benchmark comparisons.
  - A useful variance summary should keep the per-sample node list plus aggregate metrics such as average hops and total hop savings.
  - Markdown and CSV exports are enough for this slice because they feed README snippets, charts, and spreadsheet analysis without adding more UI surface area.
- Self-test:
  - `python3 - <<'PY'`
    `import random; print(random.Random(17).sample(['alpha','bravo','charlie','delta','echo'], 3))`
    `PY`
