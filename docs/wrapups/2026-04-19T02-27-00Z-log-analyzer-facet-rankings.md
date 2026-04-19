# Log Analyzer wrap-up — 2026-04-19 02:27 UTC

## Project
- `projects/log-analyzer`

## What changed
- added facet-aware top-IP and top-path ranking summaries to text and JSON output when `--facet-field` values are active
- added `--top-ip-facet-csv` and `--top-path-facet-csv` exports with `facet_label`, `facet_<field>`, `rank`, `count`, and time-window metadata columns
- committed a reusable `docs/artifacts/log-analyzer/facet-ranking-sample.log` plus matching CSV artifacts for portfolio/demo screenshots
- refreshed the README, learning note, and a 3-pass review log for the new facet-ranking workflow
- tightened the shipped ordering so facet groups are sorted by total request volume first, then label, which keeps busier deploy/release tags first in screenshots and exports

## Tests and reviews run
- `python3 -m py_compile projects/log-analyzer/log_analyzer.py`
- `python3 -m unittest discover -s projects/log-analyzer -p 'test_*.py'` (`89/89`)
- `python3 projects/log-analyzer/log_analyzer.py docs/artifacts/log-analyzer/facet-ranking-sample.log --facet-field env --facet-field region --top 3 --top-ip-facet-csv docs/artifacts/log-analyzer/top-ips-by-facet.csv --top-path-facet-csv docs/artifacts/log-analyzer/top-paths-by-facet.csv`
- `git diff --check`
- review log: `docs/reviews/2026-04-19-log-analyzer-facet-rankings-review.md`

## Feature commit
- `20444e6` — `feat(log-analyzer): add facet ranking exports`

## Next step
- optionally add facet-aware referrer/user-agent rankings if a future dataset needs marketer- or bot-heavy drill-downs
