# 2026-04-19 adaptive WSClock refresh

## Quick refresher
- A fixed WSClock `tau` is easy to explain, but it can be too sticky during short hot phases and too eager during scans.
- A practical adaptive heuristic can reuse the simulator's own locality signals: recent reuse-distance percentiles, recent unique-page counts, and whether phase overlap is collapsing.
- If dirty-page density is high, giving the adaptive window a little extra slack can trade some residency for fewer writebacks.
- Any adaptive schedule still needs hard caller-visible bounds so `--min-window` and `--max-window` stay trustworthy.

## Self-test commands
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare-wsclock-modes --frames 3 \
  --benchmark adaptive-phase-turnover --min-window 1 --max-window 9 --segment-length 8

python3 projects/page-replacement-lab/page_replacement_lab.py compare-wsclock-modes --frames 3 \
  --benchmark adaptive-phase-turnover --min-window 1 --max-window 4 --segment-length 8
```

## What to remember next run
- The new `adaptive-phase-turnover` benchmark is intentionally synthetic: it exists to demonstrate a clean adaptive win.
- `db-hotset-scan` is the more honest counterexample where adaptive only ties the best tuned fixed window.
- The next likely slice is multi-frame or gallery-style adaptive-vs-fixed summaries, not another single-workload comparison mode.
