# 2026-04-19 WSClock frame-budget study refresh

## Quick refresher
- A single-frame adaptive-vs-fixed comparison is useful, but it can hide where the adaptive heuristic only helps at one narrow memory budget.
- A stronger portfolio artifact is a frame-range sweep that reports `better` / `tied` / `worse` outcomes against the best fixed window, plus average faults and weighted scores across the sweep.
- The report should keep both stories: one benchmark where adaptive wins somewhere, and one benchmark where tuned-fixed still matches or beats it.
- SVG output matters here because the point is not just raw JSON; it is a slide-ready card that makes the multi-frame result easy to explain.

## Self-test commands
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py study-wsclock-modes --min-frames 2 --max-frames 6 \
  --benchmark adaptive-phase-turnover --min-window 1 --max-window 9 --segment-length 8

python3 projects/page-replacement-lab/page_replacement_lab.py study-wsclock-modes --min-frames 3 --max-frames 8 \
  --benchmark db-hotset-scan --min-window 2 --max-window 14 --segment-length 10
```

## What to remember next run
- `adaptive-phase-turnover` is still the clean demo for “adaptive helps at one notable frame budget.”
- `db-hotset-scan` is the honest counterexample where adaptive mostly ties and sometimes loses to the tuned fixed window.
- The next natural slice is folding these frame-budget study artifacts into the aggregate dashboard or gallery rather than adding more one-off reports.
